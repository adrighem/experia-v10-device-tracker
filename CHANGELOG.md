# Changelog

## [3.1.1](https://github.com/adrighem/kpn-experia-v10-integration/compare/v3.1.0...v3.1.1) (2026-05-10)


### Bug Fixes

* allow non-critical endpoints to fail on initial setup ([01027b3](https://github.com/adrighem/kpn-experia-v10-integration/commit/01027b342080261fecccd942bb8c4ad5c244a4c6))
* correct authentication service name back to sah.Device.Information ([a63816f](https://github.com/adrighem/kpn-experia-v10-integration/commit/a63816f8682736e9ec469fd6aa68c4a2a938ae69))
* correct authentication service name for new firmware ([0927fe5](https://github.com/adrighem/kpn-experia-v10-integration/commit/0927fe51a90f3c4fdb4d42994b7a7ba78b7fd5e1))
* correctly catch application-level errors (196621, 196614, 9003) to trigger session renewal ([c6c0b11](https://github.com/adrighem/kpn-experia-v10-integration/commit/c6c0b11e093dfe1f177a2d168d5d380a727bd1f4))
* correctly scope login logic inside asyncio lock ([ebc8e75](https://github.com/adrighem/kpn-experia-v10-integration/commit/ebc8e75323de65e4468d7fa2f0b69b2517dcba24))
* dataclass inheritance breaking HA core integration loading ([79eff79](https://github.com/adrighem/kpn-experia-v10-integration/commit/79eff79af87f92951f6c9822455f20487f69ef55))
* handle diverse login response structures for contextID parsing ([bd71605](https://github.com/adrighem/kpn-experia-v10-integration/commit/bd7160536980d163cf270436253043919817d9c2))
* handle partial failures gracefully without becoming unavailable or resetting state ([5cc8f54](https://github.com/adrighem/kpn-experia-v10-integration/commit/5cc8f54873d5b81c20a5f0ea3eed11211f49d715))
* re-add HTTP 403 check and exception handling for session renewal ([ab0954c](https://github.com/adrighem/kpn-experia-v10-integration/commit/ab0954c115bd5fc5d59b345c4825f1a994d4ba0d))
* restore robust original authentication handshake with fallback ([ba884ae](https://github.com/adrighem/kpn-experia-v10-integration/commit/ba884ae15b03f8e5fe7c84e143ce91802a62dee4))
* revert sensor key 'active_clients' to 'client_count' for entity backward compatibility ([b7e5177](https://github.com/adrighem/kpn-experia-v10-integration/commit/b7e5177ee6c58c8726f3711621b2e2b2720e4d9d))
* update reboot API endpoint to use NMC service ([124a7c0](https://github.com/adrighem/kpn-experia-v10-integration/commit/124a7c0d4e20b8941b249dfe8bfaa4f98f9c3448))

## [3.1.0](https://github.com/adrighem/kpn-experia-v10-integration/compare/v3.0.2...v3.1.0) (2026-05-05)


### Features

* add brand icon to README ([4ac8766](https://github.com/adrighem/kpn-experia-v10-integration/commit/4ac876660f14d44adb54ac1d93c153fc7441e1ef))
* design and implement custom brand assets (SVG icon/logo) ([e28d70b](https://github.com/adrighem/kpn-experia-v10-integration/commit/e28d70b6af17a3134427638720a351b68a5818ee))
* design custom brand assets and update documentation ([0afd840](https://github.com/adrighem/kpn-experia-v10-integration/commit/0afd84055ee97321a1b12826aa610966dc28a9e7))
* implement comprehensive router management including WAN statistics, metadata retrieval fixes, and improved device tracking ([80fb014](https://github.com/adrighem/kpn-experia-v10-integration/commit/80fb014e220080b431dc1595eaaa8a4fd223ca82))


### Bug Fixes

* resolve HACS validation issues by enabling repo features, adding topics, and providing brand assets ([18b9f75](https://github.com/adrighem/kpn-experia-v10-integration/commit/18b9f75c7ff68bf1965375655b0afa53349feaac))
