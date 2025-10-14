import json
from pathlib import Path
from log_to_jsonbin_aam_patched import upsert_manifest

def main():
    mf_dir = Path("manifests")
    count = 0
    for p in mf_dir.glob("*.json"):
        mf = json.loads(p.read_text(encoding="utf-8"))
        ok = upsert_manifest(mf)
        print(("OK" if ok else "FAIL"), p.name)
        count += 1
    print("Processed:", count, "manifests")
if __name__ == "__main__":
    main()
