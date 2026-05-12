# xsint

**A single command that searches dozens of services for whatever's public about an email, phone number, username, or other identifier.**

Give it one piece of information — `someone@example.com`, `+14155551234`, `johndoe`, `8.8.8.8` — and `xsint` quietly asks dozens of websites at once: *"do you know this?"* Then it prints what came back, grouped by source.

It's the kind of tool a journalist might use to vet a tip, a security team might use to investigate a phishing email, or a person might run on themselves to see what's leaking online.

## What it can find

- **Which services someone has an account on.** Spotify, Adobe, GitHub, Pinterest, Apple TV, Mixcloud, Letterboxd, Coursera, and 60+ others. If an email is registered, you'll see it.
- **Public profile info.** GitHub usernames, Google profile data, sometimes a partially-masked phone number a service has on file.
- **Data breach hits.** If the email or phone has shown up in a known breach (HaveIBeenPwned, IntelX, etc.), it'll say which.
- **Phone & address details.** Country, carrier, line type, and timezone for a phone number; coordinates for a street address.

## Install

On Mac or Linux:

```bash
curl -fsSL https://raw.githubusercontent.com/h1lw/xsint/main/install.sh | sh
```

You need Python 3.10 or newer. The installer handles everything else.

### On an iPhone (iSH)

[iSH](https://ish.app) gives you an Alpine Linux shell on iOS. xsint runs there, with the same one-liner:

```sh
apk add curl
curl -fsSL https://raw.githubusercontent.com/h1lw/xsint/main/install.sh | sh
```

The installer detects iSH automatically and:

- Installs Python and build deps via `apk`
- Skips `ghunt` and `gitfive` (their Rust/native dep chains don't build well under iSH's emulated x86). Everything else — email enumeration, HIBP, phone/IP lookups, IntelX, 9Ghz, etc. — works.

To force-install the extras anyway (slow, may fail):

```sh
curl -fsSL https://raw.githubusercontent.com/h1lw/xsint/main/install.sh | sh -s -- --with-extras
```

## Use

Hand it whatever you have:

```bash
xsint someone@example.com
xsint +14155551234
xsint johndoe
xsint 8.8.8.8
```

It runs for a few seconds, then prints what it found.

You can also force a type with a prefix when needed:

```bash
xsint email:someone@example.com
xsint phone:+14155551234
xsint user:johndoe
xsint "addr:1600 Pennsylvania Ave"
```

## A note on use

Built for journalism, security research, and looking up your own footprint. **Don't use it on people without their consent.** It only sees what services already make discoverable — it doesn't break into anything — but using it to harass, dox, or surveil someone is on you, not the tool.

## More

| Topic               | Read                                       |
| ------------------- | ------------------------------------------ |
| Detailed CLI usage  | [docs/usage.md](docs/usage.md)             |
| Full module list    | [docs/modules.md](docs/modules.md)         |
| Connecting accounts (HaveIBeenPwned key, Google login, etc.) | [docs/auth.md](docs/auth.md) |
| Running through a proxy (Tor, Burp) | [docs/proxy.md](docs/proxy.md) |
| Writing your own module | [docs/development.md](docs/development.md) |

## License

[GPL v3](LICENSE)
