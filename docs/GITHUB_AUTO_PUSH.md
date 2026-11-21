# Automatic GitHub push

This working copy is connected to `https://github.com/supraja-kotte/swadesians`.

Every local commit is automatically pushed to `origin` by the repository's local
`.git/hooks/post-commit` hook. The hook uses the installed Git executable at
`C:\Program Files\Git\cmd\git.exe` and runs `git push -u origin HEAD`.

Git can only push commits, so after editing files, commit them normally. The
post-commit hook sends that commit to GitHub immediately.

If automatic push fails, the commit is still kept locally and the hook prints
`AUTO-PUSH FAILED`. Check network access or Git credentials, then run:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' push -u origin main
```
