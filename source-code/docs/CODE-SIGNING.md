# Code signing

The installer produced by the build is currently unsigned. In practice that
means anyone who downloads it sees the blue SmartScreen page saying *"Windows
protected your PC — Unknown publisher"*, with the button to continue hidden
behind "More info". Most people stop there.

A commercial code signing certificate costs between US$ 200 and US$ 400 a year.
**SignPath** signs open source projects free of charge, and is what projects
like Notepad++ and ShareX use.

The release workflow already has the signing step in place. It stays inactive
while the secrets are missing — the release ships unsigned rather than failing —
and starts working as soon as the setup is done.

## What needs to be done

These steps require an account and decisions only the project owner can make.

**1. Apply for the free certificate**

At [signpath.org](https://signpath.org/apply), fill in the open source
application. The criteria are publicly available source, an OSI-approved licence
(MIT qualifies) and a reproducible build process — `packaging/build.ps1` and the
release workflow cover that.

Approval usually takes a few days.

**2. Configure the project in SignPath**

Once approved, create in the dashboard:

| Item | Value the workflow expects |
|---|---|
| Project slug | `ytdownloader` |
| Signing policy slug | `release-signing` |
| Artifact configuration slug | `installer` |

The artifact configuration should accept a ZIP containing `*.msi` at the root —
which is the shape `upload-artifact` produces.

**3. Store the secrets in GitHub**

Under *Settings → Secrets and variables → Actions*, add:

- `SIGNPATH_API_TOKEN`
- `SIGNPATH_ORGANIZATION_ID`

From then on, every tagged release ships signed. No workflow changes needed.

## Alternatives, if SignPath does not approve

**Commercial OV certificate** (Sectigo, DigiCert and similar): US$ 200–400 a
year. It softens the SmartScreen warning gradually, as the certificate builds
reputation — it does not remove it immediately.

**EV certificate**: more expensive, requires a hardware token or HSM, and clears
the warning from the first download. It is the option that genuinely works, but
the cost and hardware requirement are hard to justify for a project with no
revenue.

**Ship unsigned**: still works. Worth documenting in the README how to get past
the warning; the open source code and reproducible build let sceptical users
verify the binary themselves.
