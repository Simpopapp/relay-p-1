# Windows automation reliability

- [x] Replace invalid TCP receive-gap measurement with deterministic sender pacing tests.
- [x] Audit all host tests for Windows timer, file-lock and hardware assumptions (generous deadlines, no real WASAPI, temp cleanup tolerant).
- [x] Audit packaging and automatic release; packaged exe runs --self-test before publishing.
- [x] Startup fixes: server starts before phone page opens; unusable VB-Cable no longer aborts; ADB download has timeout; explicit MIME map.
- [ ] Confirm green run on GitHub Windows runner (needs the user's next push).
