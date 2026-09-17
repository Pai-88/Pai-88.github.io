# paing-hein-htet.github.io (personal site)

Single static page: `index.html` + `cv.pdf`. No build step, no JavaScript.

## Deploy to GitHub Pages (free, ~5 minutes)
1. Create a repo named exactly `Pai-88.github.io` on GitHub (public).
2. Copy `index.html` and `cv.pdf` into it, commit, push.
3. Settings → Pages → Source: "Deploy from a branch", branch `main`, folder `/`.
4. Site appears at https://pai-88.github.io within a couple of minutes.

To use a custom domain later, add a `CNAME` file containing the domain and set the DNS records GitHub shows you.

## Updating
Edit `index.html`, replace `cv.pdf` with the rebuilt one from `~/Documents/paing_cv/`, push.
