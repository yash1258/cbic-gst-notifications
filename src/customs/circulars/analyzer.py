import json
from src.core import config

class CustomsCircularAnalyzer:
    def __init__(self, target_year: str):
        self.year = str(target_year)
        self.paths = config.ensure_namespace_dirs("customs", "circulars")
        self.metadata_file = self.paths["metadata"] / f"{self.year}.json"
        
    def run(self):
        print(f"\n=====================================")
        print(f"ANALYZE YEAR {self.year} Customs Circulars (Strict Validation)")
        print(f"=====================================")
        
        if not self.metadata_file.exists():
            print(f"Metadata file {self.metadata_file} not found.")
            return None
            
        with open(self.metadata_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            circulars = data.get("circulars", [])
            
        report = {
            "expected": len(circulars),
            "english": {"available": 0, "missing": 0, "missing_reasons": {}, "list": []},
            "hindi": {"expected": sum(1 for c in circulars if c.get("docFileNameHi")), "available": 0, "missing": 0, "missing_reasons": {}, "list": []}
        }
        
        for c in circulars:
            circ_no = c.get("circularNo", "")
            if not circ_no:
                self._record_error(report, "english", c, "empty_circular_no", circ_no)
                if c.get("docFileNameHi"):
                    self._record_error(report, "hindi", c, "empty_circular_no", circ_no)
                continue
                
            category = c.get("circularCategory", "Unknown").replace(" ", "-")
            number_part = circ_no.split("/")[0] if "/" in circ_no else "unknown"
            unique_number_part = f"{number_part}_{c.get('id')}"
            
            eng_meta_path = self.paths["downloads"] / "english" / self.year / category / unique_number_part / "metadata.json"
            self._validate_path(report, "english", eng_meta_path, c, circ_no)

            if bool(c.get("docFileNameHi")):
                hin_meta_path = self.paths["downloads"] / "hindi" / self.year / category / unique_number_part / "metadata.json"
                self._validate_path(report, "hindi", hin_meta_path, c, circ_no)
                    
        return report

    def _validate_path(self, report, lang, meta_path, c, circ_no):
        if meta_path.exists():
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
                
            db_id_key = "english_db_id" if lang == "english" else "hindi_db_id"
            target_id = meta.get('id') or meta.get(db_id_key)
            
            if str(target_id) == str(c.get('id')):
                if meta.get('available'):
                    report[lang]["available"] += 1
                else:
                    reason = meta.get('missing_reason', 'missing_no_reason')
                    self._record_error(report, lang, c, reason, circ_no)
            else:
                self._record_error(report, lang, c, "overwritten_by_duplicate", circ_no, meta.get('id'))
        else:
            self._record_error(report, lang, c, "directory_not_found", circ_no)

    def _record_error(self, report, lang, c, reason, circ_no, overwritten_by=None):
        report[lang]["missing"] += 1
        report[lang]["missing_reasons"][reason] = report[lang]["missing_reasons"].get(reason, 0) + 1
        
        err = {"id": c.get("id"), "notif": circ_no, "reason": reason}
        if overwritten_by:
            err["overwritten_by"] = overwritten_by
        report[lang]["list"].append(err)
