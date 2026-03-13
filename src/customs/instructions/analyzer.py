import json
from src.core import config
from src.core.utils import slugify

class CustomsInstructionAnalyzer:
    def __init__(self, target_year: str):
        self.year = str(target_year)
        self.paths = config.ensure_namespace_dirs("customs", "instructions")
        self.metadata_file = self.paths["metadata"] / f"{self.year}.json"

    def run(self):
        print(f"\n=====================================")
        print(f"ANALYZE YEAR {self.year} Customs Instructions")
        print(f"=====================================")
        if not self.metadata_file.exists():
            print(f"Metadata file {self.metadata_file} not found."); return None
        with open(self.metadata_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            instructions = data.get("instructions", [])
        report = {
            "expected": len(instructions),
            "english": {"available": 0, "missing": 0, "missing_reasons": {}, "list": []},
            "hindi": {"expected": sum(1 for i in instructions if i.get("docFileNameHi")), "available": 0, "missing": 0, "missing_reasons": {}, "list": []}
        }
        for inst in instructions:
            inst_no = inst.get("instructionNo", "")
            cat = (inst.get("instructionCategory") or "Uncategorized").replace(" ", "-")
            if not inst_no:
                self._record_error(report, "english", inst, "empty_instruction_no", inst_no)
                continue
            number_part = inst_no.split("/")[0] if "/" in inst_no else slugify(inst_no)[:30] if inst_no else "unknown"
            unique = f"{number_part}_{inst.get('id')}"
            eng_path = self.paths["downloads"] / "english" / self.year / cat / unique / "metadata.json"
            self._validate_path(report, "english", eng_path, inst, inst_no)
            if inst.get("docFileNameHi"):
                hin_path = self.paths["downloads"] / "hindi" / self.year / cat / unique / "metadata.json"
                self._validate_path(report, "hindi", hin_path, inst, inst_no)
        return report

    def _validate_path(self, report, lang, meta_path, inst, inst_no):
        if meta_path.exists():
            with open(meta_path, 'r', encoding='utf-8') as f: meta = json.load(f)
            db_id_key = "english_db_id" if lang == "english" else "hindi_db_id"
            target_id = meta.get('id') or meta.get(db_id_key)
            if str(target_id) == str(inst.get('id')):
                if meta.get('available'): report[lang]["available"] += 1
                else: self._record_error(report, lang, inst, meta.get('missing_reason', 'missing_no_reason'), inst_no)
            else: self._record_error(report, lang, inst, "overwritten_by_duplicate", inst_no, meta.get('id'))
        else: self._record_error(report, lang, inst, "directory_not_found", inst_no)

    def _record_error(self, report, lang, inst, reason, inst_no, overwritten_by=None):
        report[lang]["missing"] += 1
        report[lang]["missing_reasons"][reason] = report[lang]["missing_reasons"].get(reason, 0) + 1
        err = {"id": inst.get("id"), "notif": inst_no, "reason": reason}
        if overwritten_by: err["overwritten_by"] = overwritten_by
        report[lang]["list"].append(err)
