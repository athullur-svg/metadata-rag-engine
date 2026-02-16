from __future__ import annotations
from typing import Any, Dict, List, Optional
import orjson
from pathlib import Path

from metadata_rag_engine.logging_conf import get_logger
from metadata_rag_engine.core.models import Table, Column

log = get_logger(__name__)

def _safe_get(d: Dict[str, Any], path: List[str]) -> Optional[Any]:
    cur: Any = d
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return None
        cur = cur[p]
    return cur

class DataHubJsonLoader:
    """
    Loads DataHub file-sink output JSON (list of events or newline-delimited JSON).
    Produces normalized Table objects (best-effort).
    """
    def load(self, input_path: str) -> List[Table]:
        p = Path(input_path)
        if not p.exists():
            raise FileNotFoundError(input_path)

        raw = p.read_bytes()

        # Support both JSON array and NDJSON
        tables: Dict[str, Table] = {}

        def handle_event(evt: Dict[str, Any]) -> None:
            entity_type = evt.get("entityType") or evt.get("entity_type")
            if entity_type != "dataset":
                return

            urn = evt.get("entityUrn") or evt.get("entity_urn") or ""
            # URN example: urn:li:dataset:(urn:li:dataPlatform:postgres,db.schema.table,PROD)
            platform = "unknown"
            name_part = urn

            if "dataPlatform:" in urn:
                try:
                    platform = urn.split("dataPlatform:")[1].split(",")[0]
                except Exception:
                    platform = "unknown"

            if "(" in urn and "," in urn:
                try:
                    name_part = urn.split(",")[1].split(",")[0].strip()
                except Exception:
                    name_part = urn

            # name_part might be "db.schema.table" or "schema.table"
            db, schema, table = None, None, name_part
            parts = name_part.split(".")
            if len(parts) >= 3:
                db, schema, table = parts[0], parts[1], ".".join(parts[2:])
            elif len(parts) == 2:
                schema, table = parts[0], parts[1]

            tkey = f"{platform}|{db}|{schema}|{table}".lower()

            if tkey not in tables:
                tables[tkey] = Table(platform=platform, database=db, schema=schema, name=table)

            aspect = evt.get("aspect", {}) or {}
            aspect_name = evt.get("aspectName") or evt.get("aspect_name")

            # schemaMetadata aspect holds fields
            if aspect_name == "schemaMetadata":
                fields = _safe_get(aspect, ["json", "fields"]) or _safe_get(aspect, ["fields"]) or []
                cols: List[Column] = []
                for f in fields:
                    col_name = f.get("fieldPath") or f.get("field_path") or f.get("nativeDataType") or f.get("name")
                    if not col_name:
                        continue
                    data_type = f.get("nativeDataType") or f.get("type") or ""
                    desc = f.get("description")
                    tags = []
                    for tg in (f.get("globalTags", {}).get("tags", []) if isinstance(f.get("globalTags"), dict) else []):
                        urn2 = tg.get("tag") or ""
                        if urn2:
                            tags.append(urn2.split(":")[-1])
                    cols.append(Column(name=str(col_name), data_type=str(data_type), description=desc, tags=tags))
                tables[tkey].columns = cols

            # datasetProperties can contain customProperties
            if aspect_name == "datasetProperties":
                cp = _safe_get(aspect, ["json", "customProperties"]) or {}
                if isinstance(cp, dict):
                    tables[tkey].properties.update({str(k): str(v) for k, v in cp.items()})

        try:
            parsed = orjson.loads(raw)
            if isinstance(parsed, list):
                for evt in parsed:
                    if isinstance(evt, dict):
                        handle_event(evt)
            elif isinstance(parsed, dict):
                handle_event(parsed)
        except orjson.JSONDecodeError:
            # NDJSON fallback
            for line in raw.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    evt = orjson.loads(line)
                    if isinstance(evt, dict):
                        handle_event(evt)
                except Exception:
                    continue

        log.info(f"Loaded {len(tables)} tables from {input_path}")
        return list(tables.values())
