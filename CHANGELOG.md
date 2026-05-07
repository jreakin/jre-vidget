# Changelog

## [0.1.4](https://github.com/jreakin/jre-vidget/compare/v0.1.3...v0.1.4) (2026-05-07)


### Features

* split CLI publish flow, add helpers, and tighten ([001d264](https://github.com/jreakin/jre-vidget/commit/001d264451b03d7a494b52bc8a582eb9a292417b))


### Documentation

* add YouTube/Google OAuth setup and update state ([e612787](https://github.com/jreakin/jre-vidget/commit/e61278752324d08bf788af09f373f18cdc39b72c))
* add YouTube/Google OAuth setup and update state ([8d0ca66](https://github.com/jreakin/jre-vidget/commit/8d0ca66051824a54631c3a8fc121ab79309ff3bd))
* add, CodeQL and Dependabot config files ([3ea66dd](https://github.com/jreakin/jre-vidget/commit/3ea66ddeec057100bedd3084483004a15b90357e))
* add, CodeQL and Dependabot config files ([4dd52a7](https://github.com/jreakin/jre-vidget/commit/4dd52a787aa56fb715b5f620babc169065dd3eb4))

## [0.1.3](https://github.com/jreakin/jre-vidget/compare/v0.1.2...v0.1.3) (2026-05-04)


### Features

* add Vitest, UI smoke tests, and GitHub dispatch helper ([12f0e26](https://github.com/jreakin/jre-vidget/commit/12f0e26291fd74b9886f087fed1b828db39dee72))
* add/tests and tighten yt-dlp coercion ([1308898](https://github.com/jreakin/jre-vidget/commit/1308898f46f159005fc52d26c401c38cbda13fff))
* **auth/engine:** prefer non- env; robust output path resolve ([9c21544](https://github.com/jreakin/jre-vidget/commit/9c21544e600d1dba8d9de174ccc1e2be1f290f50))
* **cli:** handle/login errors; fix logging behavior ([252c008](https://github.com/jreakin/jre-vidget/commit/252c008e81e3732cb23efb44932f1710104bff13))
* **cli:** improve progress hook docs and JSON output helpers ([e4a7bd6](https://github.com/jreakin/jre-vidget/commit/e4a7bd6010edc643038dbcf18b7a1f03ed80379c))
* **cli:** rename internal helpers, add log formatter tests ([ca0599b](https://github.com/jreakin/jre-vidget/commit/ca0599bc70236cf3d33256b6201ebfe8caf1b1c1))
* coerce yt-d fields rename checks, tighten config docs ([fd1a2af](https://github.com/jreakin/jre-vidget/commit/fd1a2af6c3eaa479edb2929e00d2dc675ec3c3db))


### Bug Fixes

* **config:** switch to jre_vidget.config load/save helpers ([32dd331](https://github.com/jreakin/jre-vidget/commit/32dd3315357e45eb671d142c06580350ffcd43c1))


### Documentation

* clarify Web UI PAT risk and update docs/metadata ([82c8bd9](https://github.com/jreakin/jre-vidget/commit/82c8bd9c9d7560814f09be45498bd887ea3774ea))


### Refactors

* **config:** centralize load/save and remove model I/O ([7f5dd93](https://github.com/jreakin/jre-vidget/commit/7f5dd93dcaca0eab8bbac54dc5613a044f4db759))

## [0.1.2](https://github.com/jreakin/jre-vidget/compare/v0.1.1...v0.1.2) (2026-05-04)


### Refactors

* **cli:** simplify doc and CI workflows ([c9f91a7](https://github.com/jreakin/jre-vidget/commit/c9f91a7816d7ada2997688b8cafb3042c737f0b2))
* **cli:** simplify doc and CI workflows ([65bc8ad](https://github.com/jreakin/jre-vidget/commit/65bc8ade78980a1f4e2965fe77ef148ab7b4d784))

## [0.1.1](https://github.com/jreakin/jre-vidget/compare/v0.1.0...v0.1.1) (2026-05-04)


### Features

* add Actions publish workflow, web UI, and error reporting ([1dad531](https://github.com/jreakin/jre-vidget/commit/1dad5310e4e10822d2b44a243a28547dbefb5574))
* add bootstrap workflow and getting-started docs ([92b6171](https://github.com/jreakin/jre-vidget/commit/92b617144efe48caa7a938c29cc35b92d8e4ea1f))
* add Cloudflare OAuth proxy worker (vidget-auth) ([#13](https://github.com/jreakin/jre-vidget/issues/13)) ([bd9c4bb](https://github.com/jreakin/jre-vidget/commit/bd9c4bb14077f21f87329f9c285c3c5c9584d3ec))
* add headless confirmations retries, and OAuth port ([67454d1](https://github.com/jreakin/jre-vidget/commit/67454d15488c9ac7a03712963d250d3333cd865d))
* add YouTube publish models and CLI integration ([a997ec2](https://github.com/jreakin/jre-vidget/commit/a997ec2406edf571ebe3b8882207a13cd4024422))
* CONFIG_PATH to config module and update imports ([9439aab](https://github.com/jreakin/jre-vidget/commit/9439aab2602ebfa60ffad2ba6f46c4ceb454e04c))
* **config:** store OAuth secrets as SecretStr and reveal when saving ([5a0a323](https://github.com/jreakin/jre-vidget/commit/5a0a3239cc62fbb0ec878e9fd925df47aa050587))
* **pre:** add metadata-only preview endpoint and tests ([298f572](https://github.com/jreakin/jre-vidget/commit/298f572579e77fbb4dd783c52d74b8d978a0d211))
* rework self-host onboarding around setup-secrets script ([#14](https://github.com/jreakin/jre-vidget/issues/14)) ([e330fae](https://github.com/jreakin/jre-vidget/commit/e330faef40120524ce8ab51f949d3fce80781e49))
* **ui:** add setup wizard PAT validation UI ([fa58ba6](https://github.com/jreakin/jre-vidget/commit/fa58ba639390f5270a09cafa7234a219d60061c6))
* **ui:** add web UI, deploy workflows, and publish CLI ([eadd478](https://github.com/jreakin/jre-vidget/commit/eadd47884f41476c636957ed25cdb1965913b3dd))


### Bug Fixes

* clear leftover merge conflict markers in 7 files ([#10](https://github.com/jreakin/jre-vidget/issues/10)) ([541922b](https://github.com/jreakin/jre-vidget/commit/541922be90d47bfb5dde3e2fbdbed3def8129c76))
* **cli:** resolve merge conflicts, restore helpers and config ([a39a504](https://github.com/jreakin/jre-vidget/commit/a39a5044b0c041f2bef35129445ef17941805b56))
