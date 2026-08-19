"""
GPRbase API client — access the free GPR dataset catalogue from Python.

GPRbase (https://www.gprbase.com) publishes real-world Ground Penetrating Radar
field data recorded with GSSI equipment, released under CC BY-NC-SA 4.0.

This client uses the Python standard library only. No dependencies.

Basic usage
-----------
    from gprbase import GPRbase

    gpr = GPRbase()

    for d in gpr.datasets(application="beton"):
        print(d.id, d.title)

    ds = gpr.dataset("ds016")
    print(ds.citation_apa())

Command line
------------
    python gprbase.py list
    python gprbase.py list --application reseaux --antenna "UtilityScan DF"
    python gprbase.py show ds016
    python gprbase.py csv > datasets.csv

Licence: MIT. The client is MIT; the datasets it points to are CC BY-NC-SA 4.0.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Iterator, Sequence

__version__ = "1.0.0"
__all__ = ["GPRbase", "Dataset", "GPRbaseError", "APPLICATIONS"]

DEFAULT_BASE_URL = "https://www.gprbase.com"
USER_AGENT = f"gprbase-api-client/{__version__} (+https://www.gprbase.com)"

#: Canonical application keys used by the catalogue, with English labels.
APPLICATIONS = {
    "beton": "Reinforced concrete / Civil engineering",
    "reseaux": "Underground utilities",
    "geotech": "Geotechnical investigation",
    "archeologie": "Archaeology and built heritage",
    "routes": "Roads and pavements",
    "geosciences": "Geosciences",
}


class GPRbaseError(RuntimeError):
    """Raised when the catalogue cannot be read."""


def _norm(value: str) -> str:
    """Lowercase, strip accents and punctuation — used for tolerant matching."""
    table = str.maketrans(
        "àáâäèéêëìíîïòóôöùúûüçñ",
        "aaaaeeeeiiiioooouuuucn",
    )
    return "".join(
        c for c in value.lower().translate(table) if c.isalnum()
    )


@dataclass
class Dataset:
    """One GPR dataset, as described by the catalogue.

    Attributes mirror the API fields. ``raw`` keeps the untouched payload so
    that fields added later remain reachable without upgrading this client.
    """

    id: str
    title: str = ""
    title_fr: str = ""
    description: str = ""
    description_fr: str = ""
    applications: list[str] = field(default_factory=list)
    antenna: str = ""
    frequency_mhz: str = ""
    manufacturer: str = "GSSI"
    format: str = "DZT"
    data_type: str = "raw"
    file_count: int | None = None
    targets: list[str] = field(default_factory=list)
    contributor: str = ""
    date_published: str | None = None
    license: str = ""
    status: str = "public"
    is_accessible_for_free: bool = True
    is_accessible_for_pro: bool = False
    url: str | None = None
    url_fr: str | None = None
    publisher: str = "GPRbase"
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    # ---------------------------------------------------------------- factory
    @classmethod
    def from_json(cls, payload: dict[str, Any]) -> "Dataset":
        return cls(
            id=payload.get("id", ""),
            title=payload.get("title") or "",
            title_fr=payload.get("title_fr") or "",
            description=payload.get("description") or "",
            description_fr=payload.get("description_fr") or "",
            applications=list(payload.get("applications") or []),
            antenna=payload.get("antenna") or "",
            frequency_mhz=str(payload.get("frequency_mhz") or ""),
            manufacturer=payload.get("manufacturer") or "GSSI",
            format=payload.get("format") or "DZT",
            data_type=payload.get("dataType") or "raw",
            file_count=payload.get("fileCount"),
            targets=list(payload.get("targets") or []),
            contributor=payload.get("contributor") or "",
            date_published=payload.get("datePublished"),
            license=payload.get("license") or "",
            status=payload.get("status") or "public",
            is_accessible_for_free=bool(payload.get("isAccessibleForFree", True)),
            is_accessible_for_pro=bool(payload.get("isAccessibleForPro", False)),
            url=payload.get("url"),
            url_fr=payload.get("url_fr"),
            publisher=payload.get("publisher") or "GPRbase",
            raw=payload,
        )

    # -------------------------------------------------------------- accessors
    @property
    def frequencies(self) -> list[str]:
        """Frequencies as a list. ``"300/800"`` and ``"2500;1500"`` both split."""
        out: list[str] = []
        for part in self.frequency_mhz.replace(";", "/").split("/"):
            part = part.strip()
            if part:
                out.append(part)
        return out

    @property
    def antennas(self) -> list[str]:
        """Antennas as a list — a dataset may combine several."""
        return [a.strip() for a in self.antenna.split(";") if a.strip()]

    @property
    def year(self) -> str | None:
        return self.date_published[:4] if self.date_published else None

    def has_application(self, application: str) -> bool:
        """Tolerant to case, accents and the French/English label."""
        target = _norm(application)
        aliases = {
            "concrete": "beton", "civilengineering": "beton",
            "utilities": "reseaux", "undergroundutilities": "reseaux",
            "reseauxenterres": "reseaux",
            "geotechnical": "geotech", "geotechnique": "geotech",
            "archaeology": "archeologie", "archeology": "archeologie",
            "heritage": "archeologie",
            "roads": "routes", "roadspavements": "routes",
            "geoscience": "geosciences",
        }
        target = aliases.get(target, target)
        return any(_norm(a) == target for a in self.applications)

    def title_in(self, lang: str = "en") -> str:
        return (self.title_fr or self.title) if lang == "fr" else (self.title or self.title_fr)

    def description_in(self, lang: str = "en") -> str:
        if lang == "fr":
            return self.description_fr or self.description
        return self.description or self.description_fr

    def url_in(self, lang: str = "en") -> str | None:
        return self.url_fr if lang == "fr" else self.url

    # -------------------------------------------------------------- citations
    def _equipment(self) -> str:
        bits = [self.manufacturer, self.antenna]
        if self.frequency_mhz:
            bits.append(f"{self.frequency_mhz} MHz")
        return ", ".join(b for b in bits if b)

    def citation_apa(self) -> str:
        """APA-style citation. Author is the publishing organisation."""
        author = "MDS - Le Matériel de Sondage - GPRbase"
        year = self.year or "n.d."
        out = f"{author} ({year}). {self.title} [Data set]. GPRbase."
        equip = self._equipment()
        if equip:
            out += f" {equip}."
        if self.contributor and self.contributor.lower() not in ("mds", "mdslab", "gprbase"):
            out += f" Data acquired by {self.contributor}."
        if self.url:
            out += f" {self.url}"
        return out

    def citation_bibtex(self) -> str:
        key = "".join(c for c in self.id.lower() if c.isalnum())
        note = [self._equipment(), "Licensed under CC BY-NC-SA 4.0"]
        return (
            f"@misc{{gprbase_{key},\n"
            f"  author       = {{MDS - Le Matériel de Sondage - GPRbase}},\n"
            f"  title        = {{{self.title}}},\n"
            f"  year         = {{{self.year or 'n.d.'}}},\n"
            f"  publisher    = {{GPRbase}},\n"
            f"  howpublished = {{\\url{{{self.url or ''}}}}},\n"
            f"  note         = {{{'. '.join(n for n in note if n)}}},\n"
            f"}}"
        )

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return f"{self.id} — {self.title}"


class GPRbase:
    """Read-only client for the public GPRbase catalogue.

    The catalogue is fetched once and kept in memory. Call :meth:`refresh`
    to fetch it again.
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = 20,
        token: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.token = token
        self._catalog: dict[str, Any] | None = None

    # ------------------------------------------------------------------ http
    def _get(self, path: str) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        if self.token:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}token={self.token}"
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise GPRbaseError(f"HTTP {exc.code} for {url}") from exc
        except urllib.error.URLError as exc:
            raise GPRbaseError(f"Cannot reach {url}: {exc.reason}") from exc
        except json.JSONDecodeError as exc:
            raise GPRbaseError(f"Invalid JSON from {url}") from exc

    # --------------------------------------------------------------- catalog
    def catalog(self, refresh: bool = False) -> dict[str, Any]:
        """Full catalogue payload, including ``count`` and ``generatedAt``."""
        if self._catalog is None or refresh:
            self._catalog = self._get("/api/datasets.json")
        return self._catalog

    def refresh(self) -> dict[str, Any]:
        return self.catalog(refresh=True)

    def load_from_file(self, path: str) -> dict[str, Any]:
        """Use a saved copy of the catalogue — handy offline or in tests."""
        with open(path, encoding="utf-8") as handle:
            self._catalog = json.load(handle)
        return self._catalog

    # -------------------------------------------------------------- querying
    def datasets(
        self,
        application: str | None = None,
        antenna: str | None = None,
        frequency: str | None = None,
        contributor: str | None = None,
        search: str | None = None,
        free_only: bool = True,
    ) -> list[Dataset]:
        """Datasets matching every filter given. Filters left to ``None`` are ignored.

        ``free_only`` keeps only freely accessible datasets, which is what an
        anonymous caller receives anyway.
        """
        items = [Dataset.from_json(d) for d in self.catalog().get("datasets", [])]

        if free_only:
            items = [d for d in items if d.is_accessible_for_free]
        if application:
            items = [d for d in items if d.has_application(application)]
        if antenna:
            needle = _norm(antenna)
            items = [d for d in items if any(needle in _norm(a) for a in d.antennas)]
        if frequency:
            needle = str(frequency).strip()
            items = [d for d in items if needle in d.frequencies]
        if contributor:
            needle = _norm(contributor)
            items = [d for d in items if needle in _norm(d.contributor)]
        if search:
            needle = _norm(search)
            items = [
                d for d in items
                if needle in _norm(" ".join([
                    d.title, d.title_fr, d.description, d.description_fr,
                    d.antenna, " ".join(d.targets),
                ]))
            ]
        return items

    def dataset(self, dataset_id: str) -> Dataset:
        """One dataset by identifier, fetched from its own endpoint.

        The single-dataset endpoint returns ready-made citations, which the
        catalogue does not include.
        """
        payload = self._get(f"/api/datasets/{dataset_id}.json")
        if "error" in payload:
            raise GPRbaseError(f"Dataset {dataset_id} not found or not public")
        return Dataset.from_json(payload)

    def applications(self) -> dict[str, int]:
        """How many datasets per application key."""
        counts: dict[str, int] = {}
        for d in self.datasets():
            for app in d.applications:
                counts[app] = counts.get(app, 0) + 1
        return dict(sorted(counts.items(), key=lambda kv: -kv[1]))

    def antennas(self) -> dict[str, int]:
        """How many datasets per antenna."""
        counts: dict[str, int] = {}
        for d in self.datasets():
            for antenna in d.antennas:
                counts[antenna] = counts.get(antenna, 0) + 1
        return dict(sorted(counts.items(), key=lambda kv: -kv[1]))

    # ---------------------------------------------------------------- export
    def to_csv(self, stream, datasets: Sequence[Dataset] | None = None) -> None:
        """Write a flat CSV, one row per dataset."""
        rows = list(datasets) if datasets is not None else self.datasets()
        writer = csv.writer(stream)
        writer.writerow([
            "id", "title", "title_fr", "applications", "antenna",
            "frequency_mhz", "format", "contributor", "date_published", "url",
        ])
        for d in rows:
            writer.writerow([
                d.id, d.title, d.title_fr, ";".join(d.applications), d.antenna,
                d.frequency_mhz, d.format, d.contributor, d.date_published or "",
                d.url or "",
            ])

    def __iter__(self) -> Iterator[Dataset]:
        return iter(self.datasets())

    def __len__(self) -> int:
        return len(self.datasets())


# --------------------------------------------------------------------- CLI
def _cli(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="gprbase",
        description="Browse the GPRbase catalogue of free GPR datasets.",
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--file", help="read a saved catalogue instead of the network")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="list datasets")
    p_list.add_argument("--application", choices=sorted(APPLICATIONS))
    p_list.add_argument("--antenna")
    p_list.add_argument("--frequency")
    p_list.add_argument("--contributor")
    p_list.add_argument("--search")
    p_list.add_argument("--lang", choices=["en", "fr"], default="en")

    p_show = sub.add_parser("show", help="show one dataset")
    p_show.add_argument("id")
    p_show.add_argument("--lang", choices=["en", "fr"], default="en")
    p_show.add_argument("--bibtex", action="store_true")

    sub.add_parser("stats", help="counts per application and antenna")
    sub.add_parser("csv", help="write the catalogue as CSV to stdout")

    args = parser.parse_args(argv)
    client = GPRbase(base_url=args.base_url)
    if args.file:
        client.load_from_file(args.file)

    try:
        if args.command == "list":
            found = client.datasets(
                application=args.application,
                antenna=args.antenna,
                frequency=args.frequency,
                contributor=args.contributor,
                search=args.search,
            )
            for d in found:
                freq = f"{d.frequency_mhz} MHz" if d.frequency_mhz else ""
                print(f"{d.id}  {d.title_in(args.lang)}")
                print(f"        {d.antenna} {freq} · {', '.join(d.applications)}")
            print(f"\n{len(found)} dataset(s)")

        elif args.command == "show":
            d = client.dataset(args.id)
            print(f"{d.id} — {d.title_in(args.lang)}\n")
            desc = d.description_in(args.lang)
            if desc:
                print(desc + "\n")
            print(f"Antenna      {d.antenna}")
            print(f"Frequency    {d.frequency_mhz} MHz")
            print(f"Applications {', '.join(d.applications)}")
            print(f"Contributor  {d.contributor}")
            print(f"Licence      {d.license}")
            print(f"URL          {d.url_in(args.lang) or '-'}\n")
            print(d.citation_bibtex() if args.bibtex else d.citation_apa())

        elif args.command == "stats":
            print("Datasets per application")
            for key, n in client.applications().items():
                print(f"  {n:3d}  {key:<14} {APPLICATIONS.get(key, '')}")
            print("\nDatasets per antenna")
            for key, n in client.antennas().items():
                print(f"  {n:3d}  {key}")

        elif args.command == "csv":
            client.to_csv(sys.stdout)

    except GPRbaseError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli())
