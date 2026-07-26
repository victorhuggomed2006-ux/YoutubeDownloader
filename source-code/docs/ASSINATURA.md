# Assinatura de código

*[English version below](#code-signing)*

O instalador que sai hoje do build não é assinado. Na prática, isso significa
que quem baixa vê a tela azul do SmartScreen dizendo *"O Windows protegeu o seu
computador — Editor desconhecido"*, com o botão de continuar escondido atrás de
"Mais informações". A maior parte das pessoas desiste nesse ponto.

Um certificado comercial de assinatura custa entre US$ 200 e US$ 400 por ano. O
**SignPath** assina projetos de código aberto sem cobrar, e é o que usam
projetos como Notepad++ e ShareX.

O workflow de release já tem a etapa de assinatura pronta. Ela fica inativa
enquanto os segredos não existirem — o release sai sem assinatura em vez de
falhar — e passa a funcionar assim que o cadastro estiver feito.

## O que precisa ser feito

Estes passos exigem uma conta e decisões que só o dono do projeto pode tomar.

**1. Solicitar o certificado gratuito**

Em [signpath.org](https://signpath.org/apply), preencha a solicitação para
projetos de código aberto. Os critérios são ter o código publicamente
disponível, uma licença aprovada pela OSI (a MIT atende) e um processo de build
reproduzível — o `packaging/build.ps1` e o workflow de release cobrem isso.

A aprovação costuma levar alguns dias.

**2. Configurar o projeto no SignPath**

Depois de aprovado, crie no painel:

| Item | Valor esperado pelo workflow |
|---|---|
| Project slug | `ytdownloader` |
| Signing policy slug | `release-signing` |
| Artifact configuration slug | `instaladores` |

A configuração de artefato deve aceitar um arquivo ZIP contendo `*.exe` e
`*.msi` na raiz — que é o formato que o `upload-artifact` produz.

**3. Guardar os segredos no GitHub**

Em *Settings → Secrets and variables → Actions*, adicione:

- `SIGNPATH_API_TOKEN`
- `SIGNPATH_ORGANIZATION_ID`

A partir daí, todo release publicado por tag sai assinado. Não é preciso mexer
no workflow.

## Alternativas, se o SignPath não aprovar

**Certificado OV comercial** (Sectigo, DigiCert e similares): entre US$ 200 e
US$ 400 por ano. Reduz o alerta do SmartScreen aos poucos, conforme o
certificado ganha reputação — não elimina de imediato.

**Certificado EV**: mais caro, exige token físico ou HSM, e elimina o alerta
desde o primeiro download. É o que faz diferença de verdade, mas o custo e a
exigência de hardware o tornam difícil de justificar num projeto sem receita.

**Não assinar**: continua funcionando. Vale documentar no README como passar
pelo aviso, e o fato de o código ser aberto e o build reproduzível ajuda quem
desconfia a verificar por conta própria.

---

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
| Artifact configuration slug | `instaladores` |

The artifact configuration should accept a ZIP containing `*.exe` and `*.msi` at
the root — which is the shape `upload-artifact` produces.

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
