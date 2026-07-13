#![allow(non_snake_case)]

use std::cmp::Ordering;
use std::collections::{BTreeSet, HashMap};
use std::ffi::{c_char, c_int, c_void, CStr, CString};
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::mem::size_of;
use std::path::{Path, PathBuf};
use std::ptr::null_mut;
use std::slice;
use std::sync::atomic::{AtomicBool, Ordering as AtomicOrdering};

const CONFIG_FILE: &str = "saeko_mod_loader.ini";
const LOG_FILE: &str = "saeko_mod_loader_linux.log";
const DEFAULT_TARGET_LANG: &str = "pl";
const DEFAULT_FALLBACK_LANG: &str = "en";
const DEFAULT_LANG_LABEL: &str = "Polski";
const DEFAULT_TRANSLATION_DIR: &str = "saeko_mod_loader/lang";
const EMPTY_LANG_LABEL: &str = "None";
const MAX_EMBED_PATH: usize = 260;
const MAX_EMBED_DATA: usize = 100_000_000;
const RTLD_NOW: c_int = 2;
const PROT_READ: c_int = 0x1;
const PROT_WRITE: c_int = 0x2;
const PROT_EXEC: c_int = 0x4;
const _SC_PAGESIZE: c_int = 30;

static INIT_DONE: AtomicBool = AtomicBool::new(false);
static mut LOADER_STATE: *mut LoaderState = null_mut();

#[repr(C)]
struct DlInfo {
    dli_fname: *const c_char,
    dli_fbase: *mut c_void,
    dli_sname: *const c_char,
    dli_saddr: *mut c_void,
}

extern "C" {
    fn dladdr(addr: *const c_void, info: *mut DlInfo) -> c_int;
    fn dlopen(filename: *const c_char, flags: c_int) -> *mut c_void;
    fn dlsym(handle: *mut c_void, symbol: *const c_char) -> *mut c_void;
    fn mprotect(addr: *mut c_void, len: usize, prot: c_int) -> c_int;
    fn sysconf(name: c_int) -> isize;
}

#[used]
#[cfg_attr(target_os = "linux", link_section = ".init_array")]
static INIT_ARRAY: extern "C" fn() = linux_ctor;

extern "C" fn linux_ctor() {
    SaekoModLoaderLinuxInit();
}

#[no_mangle]
pub extern "C" fn SaekoModLoaderLinuxInit() {
    if INIT_DONE.swap(true, AtomicOrdering::SeqCst) {
        return;
    }
    let dir = module_dir().unwrap_or_else(|| PathBuf::from("."));
    if let Err(err) = run_loader(&dir) {
        log_line(&dir, &format!("ERROR: {err}"));
    }
}

#[repr(C)]
#[derive(Clone, Copy)]
struct EmbedFile {
    name_ptr: usize,
    name_len: usize,
    data_ptr: usize,
    data_len: usize,
    hash: [u8; 16],
}

#[repr(C)]
#[derive(Clone, Copy)]
struct GoSlice {
    data: usize,
    len: usize,
    cap: usize,
}

#[repr(C)]
#[derive(Clone, Copy)]
struct LanguageEntry {
    code_ptr: usize,
    code_len: usize,
    label_ptr: usize,
    label_len: usize,
}

#[derive(Clone)]
struct LoaderConfig {
    mods_enabled: bool,
    target_lang: String,
    fallback_lang: String,
    language_label: String,
    translation_dir: PathBuf,
}

#[derive(Clone)]
struct MapRegion {
    start: usize,
    end: usize,
    readable: bool,
    executable: bool,
    path: Option<PathBuf>,
}

#[derive(Clone)]
struct FoundRecord {
    table_ptr: usize,
    name: String,
}

struct EmbedLayout {
    slice_ptr: usize,
    records: Vec<FoundRecord>,
}

struct LanguageLayout {
    slice_ptr: usize,
    entries: Vec<LanguageEntry>,
}

struct LoaderState {
    _names: Vec<Box<[u8]>>,
    _payloads: Vec<Box<[u8]>>,
    _records: Box<[EmbedFile]>,
    _language_code: Box<[u8]>,
    _language_label: Box<[u8]>,
    _languages: Box<[LanguageEntry]>,
}

fn run_loader(dir: &Path) -> Result<(), String> {
    let config = load_config(dir);
    log_line(
        dir,
        &format!(
            "linux loader starting: mods_enabled={} language={} label={} fallback={} translation_dir={}",
            config.mods_enabled,
            config.target_lang,
            config.language_label,
            config.fallback_lang,
            config.translation_dir.display()
        ),
    );

    let maps = read_maps()?;
    let exe = fs::read_link("/proc/self/exe").map_err(|err| format!("readlink exe failed: {err}"))?;
    let exe_regions = executable_regions(&maps, &exe);
    if exe_regions.is_empty() {
        return Err(format!("could not find mapped executable regions for {}", exe.display()));
    }

    let embed = unsafe { find_embed_layout(&exe_regions)? };
    let language = unsafe { find_language_layout(&exe_regions)? };
    log_line(
        dir,
        &format!(
            "found embed.FS records={}, language_entries={}",
            embed.records.len(),
            language.entries.len()
        ),
    );

    if !config.mods_enabled || unsafe { language_has_code(&language, &config.target_lang) } {
        let loaded = load_external_so_mods(dir);
        log_line(dir, &format!("custom language injection skipped; external_so_loaded={loaded}"));
        return Ok(());
    }

    let translation_dir = if config.translation_dir.is_absolute() {
        config.translation_dir.clone()
    } else {
        dir.join(&config.translation_dir)
    };
    let expected = expected_translation_files(&embed.records, &config.fallback_lang);
    if expected.is_empty() {
        return Err(format!("could not discover {} CSV list", config.fallback_lang));
    }
    let csvs = if translation_dir.exists() {
        collect_csvs(&translation_dir).map_err(|err| format!("failed to read CSV files: {err}"))?
    } else {
        Vec::new()
    };
    let ready = csvs
        .iter()
        .filter(|(rel, _)| expected.iter().any(|expected_rel| expected_rel == rel))
        .count();
    let label = if ready == expected.len() {
        config.language_label.clone()
    } else {
        EMPTY_LANG_LABEL.to_string()
    };
    log_line(
        dir,
        &format!("translation status: {ready}/{} files ready, menu_label={label}", expected.len()),
    );

    let (mut state, record_count) = unsafe { build_state(&embed.records, csvs, &expected, &config)? };
    let records_ptr = state._records.as_ptr() as usize;
    let (language_count, language_ptr) =
        unsafe { prepare_language_list(&language, &mut state, &config.target_lang, &label)? };

    unsafe {
        patch_slice(embed.slice_ptr, records_ptr, record_count, &exe_regions)?;
        patch_slice(language.slice_ptr, language_ptr, language_count, &exe_regions)?;
    }
    unsafe {
        LOADER_STATE = Box::into_raw(Box::new(state));
    }
    let loaded = load_external_so_mods(dir);
    log_line(
        dir,
        &format!(
            "linux loader ready: records={}, languages={}, external_so_loaded={}",
            record_count, language_count, loaded
        ),
    );
    Ok(())
}

fn load_config(dir: &Path) -> LoaderConfig {
    let mut config = LoaderConfig {
        mods_enabled: true,
        target_lang: DEFAULT_TARGET_LANG.to_string(),
        fallback_lang: DEFAULT_FALLBACK_LANG.to_string(),
        language_label: DEFAULT_LANG_LABEL.to_string(),
        translation_dir: PathBuf::from(DEFAULT_TRANSLATION_DIR),
    };
    let path = dir.join(CONFIG_FILE);
    let Ok(text) = fs::read_to_string(path) else {
        return config;
    };
    for raw in text.lines() {
        let line = raw.trim();
        if line.is_empty() || line.starts_with('#') || line.starts_with(';') || line.starts_with('[') {
            continue;
        }
        let Some((key, value)) = line.split_once('=') else {
            continue;
        };
        let key = key.trim().to_ascii_lowercase();
        let value = value.trim().trim_matches('"').trim_matches('\'');
        match key.as_str() {
            "mods_enabled" | "enabled" => config.mods_enabled = parse_bool(value, config.mods_enabled),
            "language_code" | "target_lang" => config.target_lang = value.to_ascii_lowercase(),
            "fallback_language" | "fallback_lang" => config.fallback_lang = value.to_ascii_lowercase(),
            "language_label" | "label" => config.language_label = value.to_string(),
            "translation_dir" => config.translation_dir = PathBuf::from(value),
            _ => {}
        }
    }
    config
}

fn parse_bool(value: &str, default: bool) -> bool {
    match value.trim().to_ascii_lowercase().as_str() {
        "1" | "true" | "yes" | "on" | "enabled" => true,
        "0" | "false" | "no" | "off" | "disabled" => false,
        _ => default,
    }
}

unsafe fn find_embed_layout(regions: &[MapRegion]) -> Result<EmbedLayout, String> {
    let mut candidates = Vec::new();
    for region in regions.iter().filter(|region| region.readable) {
        let mut ptr = region.start;
        while ptr + size_of::<EmbedFile>() <= region.end {
            let record = &*(ptr as *const EmbedFile);
            if record.name_len > 0
                && record.name_len <= MAX_EMBED_PATH
                && record.data_len <= MAX_EMBED_DATA
                && range_in_regions(regions, record.name_ptr, record.name_len)
                && (record.data_len == 0 || range_in_regions(regions, record.data_ptr, record.data_len))
            {
                if let Some(name) = read_utf8(record.name_ptr, record.name_len) {
                    if name == "full_cmp" || name.starts_with("full_cmp/") {
                        candidates.push(FoundRecord { table_ptr: ptr, name });
                    }
                }
            }
            ptr += 8;
        }
    }
    if candidates.is_empty() {
        return Err("could not find embed.FS records".to_string());
    }
    candidates.sort_by_key(|record| record.table_ptr);
    let mut best_start = 0;
    let mut best_len = 1;
    let mut run_start = 0;
    for index in 1..candidates.len() {
        if candidates[index].table_ptr != candidates[index - 1].table_ptr + size_of::<EmbedFile>() {
            let run_len = index - run_start;
            if run_len > best_len {
                best_start = run_start;
                best_len = run_len;
            }
            run_start = index;
        }
    }
    let final_len = candidates.len() - run_start;
    if final_len > best_len {
        best_start = run_start;
        best_len = final_len;
    }
    let records = candidates[best_start..best_start + best_len].to_vec();
    if records.len() < 100 {
        return Err(format!("embed.FS run too small: {}", records.len()));
    }
    let array_ptr = records[0].table_ptr;
    let slice_ptr = find_slice_header(regions, array_ptr, records.len())?;
    Ok(EmbedLayout { slice_ptr, records })
}

unsafe fn find_language_layout(regions: &[MapRegion]) -> Result<LanguageLayout, String> {
    const CODES: [&str; 9] = ["ja", "en", "zh-cn", "zh-tw", "fr", "de", "ru", "uk", "pt-br"];
    let mut candidates = Vec::new();
    for region in regions.iter().filter(|region| region.readable) {
        let mut ptr = region.start;
        while ptr + CODES.len() * size_of::<LanguageEntry>() <= region.end {
            let mut entries = Vec::with_capacity(CODES.len());
            let mut matched = true;
            for (index, expected) in CODES.iter().enumerate() {
                let entry = *((ptr + index * size_of::<LanguageEntry>()) as *const LanguageEntry);
                if entry.code_len == 0
                    || entry.code_len > 16
                    || entry.label_len == 0
                    || entry.label_len > 64
                    || !range_in_regions(regions, entry.code_ptr, entry.code_len)
                    || !range_in_regions(regions, entry.label_ptr, entry.label_len)
                    || read_utf8(entry.code_ptr, entry.code_len).as_deref() != Some(*expected)
                {
                    matched = false;
                    break;
                }
                entries.push(entry);
            }
            if matched {
                candidates.push((ptr, entries));
            }
            ptr += 8;
        }
    }
    if candidates.len() != 1 {
        return Err(format!("expected one language array, found {}", candidates.len()));
    }
    let (array_ptr, entries) = candidates.remove(0);
    let slice_ptr = find_slice_header(regions, array_ptr, entries.len())?;
    Ok(LanguageLayout { slice_ptr, entries })
}

unsafe fn find_slice_header(regions: &[MapRegion], array_ptr: usize, count: usize) -> Result<usize, String> {
    let mut hits = Vec::new();
    for region in regions.iter().filter(|region| region.readable) {
        let mut ptr = region.start;
        while ptr + size_of::<GoSlice>() <= region.end {
            let slice = &*(ptr as *const GoSlice);
            if slice.data == array_ptr && slice.len == count && slice.cap == count {
                hits.push(ptr);
            }
            ptr += 8;
        }
    }
    if hits.len() != 1 {
        return Err(format!("expected one slice header, found {}", hits.len()));
    }
    Ok(hits[0])
}

unsafe fn language_has_code(layout: &LanguageLayout, code: &str) -> bool {
    layout
        .entries
        .iter()
        .any(|entry| read_utf8(entry.code_ptr, entry.code_len).as_deref() == Some(code))
}

unsafe fn build_state(
    original_records: &[FoundRecord],
    csvs: Vec<(String, Vec<u8>)>,
    expected: &[String],
    config: &LoaderConfig,
) -> Result<(LoaderState, usize), String> {
    let original_by_name: HashMap<&str, EmbedFile> = original_records
        .iter()
        .map(|found| (found.name.as_str(), *(found.table_ptr as *const EmbedFile)))
        .collect();
    let csv_by_rel: HashMap<String, Vec<u8>> = csvs.into_iter().collect();
    let mut names = Vec::new();
    let mut payloads = Vec::new();
    let mut all = Vec::new();
    for found in original_records {
        all.push((found.name.clone(), *(found.table_ptr as *const EmbedFile)));
    }
    for rel in expected {
        let source_name = format!("full_cmp/scripts/main/{}/{rel}", config.fallback_lang);
        let target_name = format!("full_cmp/scripts/main/{}/{rel}", config.target_lang);
        let source = original_by_name
            .get(source_name.as_str())
            .ok_or_else(|| format!("fallback record missing: {source_name}"))?;
        let payload = csv_by_rel
            .get(rel)
            .cloned()
            .unwrap_or_else(|| slice::from_raw_parts(source.data_ptr as *const u8, source.data_len).to_vec());
        let name = target_name.into_bytes().into_boxed_slice();
        let payload = payload.into_boxed_slice();
        let record = EmbedFile {
            name_ptr: name.as_ptr() as usize,
            name_len: name.len(),
            data_ptr: payload.as_ptr() as usize,
            data_len: payload.len(),
            hash: [0; 16],
        };
        names.push(name);
        payloads.push(payload);
        all.push((String::from_utf8_lossy(names.last().unwrap()).to_string(), record));
    }
    let mut dirs = BTreeSet::new();
    for (name, _) in &all {
        for dir in parent_dirs(name) {
            dirs.insert(dir);
        }
    }
    for dir in dirs {
        if all.iter().any(|(name, _)| name == &dir) {
            continue;
        }
        let name = dir.into_bytes().into_boxed_slice();
        let record = EmbedFile {
            name_ptr: name.as_ptr() as usize,
            name_len: name.len(),
            data_ptr: 0,
            data_len: 0,
            hash: [0; 16],
        };
        names.push(name);
        all.push((String::from_utf8_lossy(names.last().unwrap()).to_string(), record));
    }
    all.sort_by(|left, right| embed_cmp(&left.0, &right.0));
    let records = all.into_iter().map(|(_, record)| record).collect::<Vec<_>>().into_boxed_slice();
    let count = records.len();
    Ok((
        LoaderState {
            _names: names,
            _payloads: payloads,
            _records: records,
            _language_code: Box::new([]),
            _language_label: Box::new([]),
            _languages: Box::new([]),
        },
        count,
    ))
}

unsafe fn prepare_language_list(
    layout: &LanguageLayout,
    state: &mut LoaderState,
    code: &str,
    label: &str,
) -> Result<(usize, usize), String> {
    state._language_code = code.as_bytes().to_vec().into_boxed_slice();
    state._language_label = label.as_bytes().to_vec().into_boxed_slice();
    let mut entries = layout.entries.clone();
    entries.push(LanguageEntry {
        code_ptr: state._language_code.as_ptr() as usize,
        code_len: state._language_code.len(),
        label_ptr: state._language_label.as_ptr() as usize,
        label_len: state._language_label.len(),
    });
    state._languages = entries.into_boxed_slice();
    Ok((state._languages.len(), state._languages.as_ptr() as usize))
}

unsafe fn patch_slice(
    slice_ptr: usize,
    data_ptr: usize,
    count: usize,
    regions: &[MapRegion],
) -> Result<(), String> {
    make_writable(slice_ptr, size_of::<GoSlice>(), regions)?;
    *(slice_ptr as *mut GoSlice) = GoSlice { data: data_ptr, len: count, cap: count };
    Ok(())
}

unsafe fn make_writable(ptr: usize, len: usize, regions: &[MapRegion]) -> Result<(), String> {
    let page = sysconf(_SC_PAGESIZE).max(4096) as usize;
    let start = ptr & !(page - 1);
    let end = (ptr + len + page - 1) & !(page - 1);
    let mut prot = PROT_READ | PROT_WRITE;
    if regions
        .iter()
        .any(|region| ptr >= region.start && ptr < region.end && region.executable)
    {
        prot |= PROT_EXEC;
    }
    if mprotect(start as *mut c_void, end - start, prot) != 0 {
        return Err("mprotect failed".to_string());
    }
    Ok(())
}

fn expected_translation_files(original_records: &[FoundRecord], fallback_lang: &str) -> Vec<String> {
    let prefix = format!("full_cmp/scripts/main/{fallback_lang}/");
    let mut files = BTreeSet::new();
    for record in original_records {
        if record.name.starts_with(&prefix) && record.name.ends_with(".csv") {
            files.insert(record.name[prefix.len()..].to_string());
        }
    }
    files.into_iter().collect()
}

fn collect_csvs(root: &Path) -> std::io::Result<Vec<(String, Vec<u8>)>> {
    let mut result = Vec::new();
    collect_csvs_inner(root, root, &mut result)?;
    result.sort_by(|left, right| left.0.cmp(&right.0));
    Ok(result)
}

fn collect_csvs_inner(root: &Path, current: &Path, result: &mut Vec<(String, Vec<u8>)>) -> std::io::Result<()> {
    for entry in fs::read_dir(current)? {
        let entry = entry?;
        let path = entry.path();
        if path.is_dir() {
            collect_csvs_inner(root, &path, result)?;
            continue;
        }
        if path.extension().and_then(|ext| ext.to_str()) != Some("csv") {
            continue;
        }
        let rel = path
            .strip_prefix(root)
            .unwrap_or(&path)
            .components()
            .map(|part| part.as_os_str().to_string_lossy())
            .collect::<Vec<_>>()
            .join("/");
        let mut payload = fs::read(path)?;
        if payload.starts_with(b"\xef\xbb\xbf") {
            payload.drain(..3);
        }
        result.push((rel, payload));
    }
    Ok(())
}

fn parent_dirs(name: &str) -> Vec<String> {
    let parts: Vec<&str> = name.split('/').collect();
    let mut dirs = Vec::new();
    for end in 1..parts.len() {
        dirs.push(format!("{}/", parts[..end].join("/")));
    }
    dirs
}

fn embed_cmp(left: &str, right: &str) -> Ordering {
    let (left_dir, left_elem) = embed_sort_key(left);
    let (right_dir, right_elem) = embed_sort_key(right);
    left_dir.cmp(right_dir).then_with(|| left_elem.cmp(right_elem))
}

fn embed_sort_key(name: &str) -> (&str, &str) {
    let trimmed = name.strip_suffix('/').unwrap_or(name);
    match trimmed.rsplit_once('/') {
        Some((dir, elem)) => (dir, elem),
        None => (".", trimmed),
    }
}

fn read_maps() -> Result<Vec<MapRegion>, String> {
    let text = fs::read_to_string("/proc/self/maps").map_err(|err| format!("read maps failed: {err}"))?;
    let mut maps = Vec::new();
    for line in text.lines() {
        let mut parts = line.split_whitespace();
        let Some(range) = parts.next() else { continue };
        let Some(perms) = parts.next() else { continue };
        let _offset = parts.next();
        let _dev = parts.next();
        let _inode = parts.next();
        let path = parts.next().map(PathBuf::from);
        let Some((start, end)) = range.split_once('-') else { continue };
        let Ok(start) = usize::from_str_radix(start, 16) else { continue };
        let Ok(end) = usize::from_str_radix(end, 16) else { continue };
        maps.push(MapRegion {
            start,
            end,
            readable: perms.as_bytes().get(0) == Some(&b'r'),
            executable: perms.as_bytes().get(2) == Some(&b'x'),
            path,
        });
    }
    Ok(maps)
}

fn executable_regions(maps: &[MapRegion], exe: &Path) -> Vec<MapRegion> {
    let exe_canon = exe.canonicalize().unwrap_or_else(|_| exe.to_path_buf());
    maps.iter()
        .filter(|region| {
            region.path.as_ref().is_some_and(|path| {
                path.canonicalize().map(|canon| canon == exe_canon).unwrap_or(false)
            })
        })
        .cloned()
        .collect()
}

fn range_in_regions(regions: &[MapRegion], ptr: usize, len: usize) -> bool {
    let Some(end) = ptr.checked_add(len) else { return false };
    regions.iter().any(|region| ptr >= region.start && end <= region.end && region.readable)
}

unsafe fn read_utf8(ptr: usize, len: usize) -> Option<String> {
    let bytes = slice::from_raw_parts(ptr as *const u8, len);
    std::str::from_utf8(bytes).ok().map(str::to_string)
}

fn load_external_so_mods(dir: &Path) -> usize {
    let root = dir.join("saeko_mod_loader").join("mods");
    let Ok(entries) = fs::read_dir(root) else {
        return 0;
    };
    let mut loaded = 0;
    for entry in entries.flatten() {
        let path = entry.path();
        if path.extension().and_then(|ext| ext.to_str()) != Some("so") {
            continue;
        }
        let Ok(c_path) = CString::new(path.to_string_lossy().as_bytes()) else {
            continue;
        };
        let handle = unsafe { dlopen(c_path.as_ptr(), RTLD_NOW) };
        if handle.is_null() {
            continue;
        }
        loaded += 1;
        let symbol = CString::new("SaekoModInit").unwrap();
        let init = unsafe { dlsym(handle, symbol.as_ptr()) };
        if !init.is_null() {
            let init: unsafe extern "C" fn() -> u32 = unsafe { std::mem::transmute(init) };
            let _ = unsafe { init() };
        }
    }
    loaded
}

fn module_dir() -> Option<PathBuf> {
    let mut info = DlInfo {
        dli_fname: std::ptr::null(),
        dli_fbase: null_mut(),
        dli_sname: std::ptr::null(),
        dli_saddr: null_mut(),
    };
    let ok = unsafe { dladdr(SaekoModLoaderLinuxInit as *const c_void, &mut info) };
    if ok == 0 || info.dli_fname.is_null() {
        return None;
    }
    let path = unsafe { CStr::from_ptr(info.dli_fname) }.to_string_lossy();
    PathBuf::from(path.as_ref()).parent().map(Path::to_path_buf)
}

fn log_line(dir: &Path, message: &str) {
    let path = dir.join(LOG_FILE);
    if let Ok(mut file) = OpenOptions::new().create(true).append(true).open(path) {
        let _ = writeln!(file, "{message}");
    }
}
