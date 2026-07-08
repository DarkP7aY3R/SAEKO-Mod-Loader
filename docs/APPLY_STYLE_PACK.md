# Apply the GitHub style pack

Copy these files into your local repository:

```powershell
Copy-Item -Recurse -Force ".\assets" "C:\Users\Mati\Desktop\SAEKO_GitHub\SAEKO_Mod_Loader\"
Copy-Item -Force ".\README.md" "C:\Users\Mati\Desktop\SAEKO_GitHub\SAEKO_Mod_Loader\README.md"
Copy-Item -Recurse -Force ".\docs" "C:\Users\Mati\Desktop\SAEKO_GitHub\SAEKO_Mod_Loader\"
```

Then commit:

```powershell
cd "C:\Users\Mati\Desktop\SAEKO_GitHub\SAEKO_Mod_Loader"
git add README.md assets docs
git commit -m "Add GitHub banner and official links"
git push
```

For the repository social preview:

1. Open the repository on GitHub.
2. Go to **Settings**.
3. Go to **General**.
4. Find **Social preview**.
5. Upload `assets/social-preview.png`.
