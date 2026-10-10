# Wiring up Reddit API access (2-minute setup)

The prototype scrapes public RSS feeds, which Reddit throttles hard from
datacenter IPs. Registering a free Reddit app gives proper API access:
full coverage of all 7 subs, plus comments and search, at ~60-100
requests/minute (way more than a daily scan needs).

You do this part in your browser. It needs your Reddit account.

## Register the app

1. Sign in to Reddit, then open https://www.reddit.com/prefs/apps
2. Scroll to the bottom and click "create another app..."
3. Fill in the form:
   - name: anything, e.g. "Marriott AI Monitor"
   - type: select **script** (this is the personal-use type; it gives you
     both an ID and a secret)
   - description / about url: optional, leave blank
   - redirect uri: `http://localhost:8080` (required field, not actually
     used by script apps)
4. Click "create app"
5. Copy two values from the app card:
   - **Client ID**: the short string directly under the app name, under the
     words "personal use script" (about 14 characters)
   - **Secret**: the longer string on the line labeled "secret"

## What happens next (Zuka handles this)

Hand the client ID, secret, and your Reddit username to Zuka. The monitor
script will be updated to:

1. Trade the credentials for an OAuth token
   (`POST https://www.reddit.com/api/v1/access_token`, HTTP Basic auth
   with client_id:secret, `grant_type=password` plus your username/password)
2. Call the API at `https://oauth.reddit.com` with the token
3. Store the credentials in a local config file in this folder only
   (never committed or shared anywhere)

## Two things to know first

- **2FA**: the password flow does not work if your Reddit account has
  two-factor auth on. Either use an account without 2FA, or tell Zuka and
  the code-append trick (`password:123456`) can be tried. Cleanest is a
  throwaway Reddit account used only for this monitor.
- **Scope**: a script app can only act as the account that registered it.
  For a read-only reputation scan, that is all we need.

Once the credentials are in, the same daily scan runs against the real API:
no more 429s, no more partial coverage, and comment scanning becomes
possible if you want it.
