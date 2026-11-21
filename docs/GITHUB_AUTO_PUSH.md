# Automatic GitHub push

This working copy is connected to `https://github.com/supraja-kotte/swadesians`.

Every local commit is automatically pushed to `origin` by the repository's local
`.git/hooks/post-commit` hook. The hook uses the installed Git executable at
`C:\Program Files\Git\cmd\git.exe`, forces the Windows Git Credential Manager,
and retries a failed push once.

Git can only push commits, so after editing files, commit them normally. The
post-commit hook sends that commit to GitHub immediately.

Hook output is appended to `.git/auto-push.log`. If automatic push still fails,
the commit is kept locally and the hook prints `AUTO-PUSH FAILED`. Check network
access or Git credentials, then run:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' push -u origin main
```

If you use a different clone of this repository, copy `.git/hooks/post-commit`
from this working copy into that clone's `.git/hooks` directory.
