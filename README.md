# GPRbase API client

Programmatic access to [GPRbase](https://www.gprbase.com) — a free library of
**real-world Ground Penetrating Radar datasets** recorded with GSSI equipment,
covering reinforced concrete, buried utilities, geotechnics, roads, archaeology
and geosciences.

Raw `.DZT` files, no processing, released under CC BY-NC-SA 4.0.

Python and JavaScript clients. No dependencies in either.

*[Version française plus bas](#client-api-gprbase-français)*

---

## Why this exists

GPR theory can be taught from a textbook; interpretation cannot. It is learned
by working through many real radargrams — and suitable field data are rarely
available to instructors, students or software developers.

GPRbase publishes that data. This client makes the catalogue usable from a
script: filter by application, antenna or frequency, pull metadata, generate
citations, export to CSV.

## Install

Nothing to install. Copy the single file you need.

```bash
# Python — standard library only
curl -O https://raw.githubusercontent.com/MDS-GPRbase/gprbase-api-client/main/python/gprbase.py

# JavaScript — Node 18+ or any modern browser
curl -O https://raw.githubusercontent.com/MDS-GPRbase/gprbase-api-client/main/javascript/gprbase.js
```

## Python

```python
from gprbase import GPRbase

gpr = GPRbase()

# Concrete datasets recorded with a FLEX NX antenna
for d in gpr.datasets(application="beton", antenna="FLEX NX"):
    print(d.id, d.title, d.url)

# Anything acquired at 300 MHz
for d in gpr.datasets(frequency="300"):
    print(d.id, d.applications)

# Full-text search, accent-insensitive
gpr.datasets(search="voute")     # finds "Voûtes en maçonnerie"

# One dataset, with a ready-made citation
ds = gpr.dataset("ds016")
print(ds.citation_apa())
print(ds.citation_bibtex())

# What is in the catalogue?
gpr.applications()   # {'beton': 12, 'reseaux': 5, ...}
gpr.antennas()       # {'UtilityScan DF': 9, 'FLEX NX': 5, ...}
```

### Command line

```bash
python gprbase.py list
python gprbase.py list --application reseaux --antenna "UtilityScan DF"
python gprbase.py list --search karst --lang fr
python gprbase.py show ds016 --bibtex
python gprbase.py stats
python gprbase.py csv > datasets.csv
```

## JavaScript

```javascript
import { GPRbase } from './gprbase.js';

const gpr = new GPRbase();

const concrete = await gpr.datasets({ application: 'beton', antenna: 'FLEX NX' });
concrete.forEach(d => console.log(d.id, d.title, d.url));

const ds = await gpr.dataset('ds016');
console.log(ds.citationApa());

console.log(await gpr.applications());
```

Runs unchanged in the browser:

```html
<script type="module">
  import { GPRbase } from './gprbase.js';
  const gpr = new GPRbase();
  const datasets = await gpr.datasets({ application: 'reseaux' });
  document.body.textContent = `${datasets.length} utility datasets`;
</script>
```

## Filters

| Filter | Behaviour |
|---|---|
| `application` | Tolerant: `beton`, `Béton`, `concrete` all match. Keys: `beton`, `reseaux`, `geotech`, `archeologie`, `routes`, `geosciences` |
| `antenna` | Partial match: `utilityscan` matches `UtilityScan DF` |
| `frequency` | Exact match against split values: `300` matches `300/800` |
| `contributor` | Partial match |
| `search` | Full text over titles, descriptions, antenna, targets — accent-insensitive |
| `free_only` / `freeOnly` | `true` by default |

Multi-value fields are split for you: an antenna field of `FLEX NX;NX25;NX15`
gives `["FLEX NX", "NX25", "NX15"]`, and a frequency of `300/800` gives
`["300", "800"]`.

## The API itself

The client wraps two public endpoints. Both are open, no key required.

```
GET https://www.gprbase.com/api/datasets.json        full catalogue
GET https://www.gprbase.com/api/datasets/{id}.json   one dataset + citations
```

Each dataset carries: identifiers, bilingual title and description,
applications, antenna, frequency, format, contributor, licence, publication
date, and canonical URLs in both languages.

## Licensing

The client is **MIT**. The datasets it points to are **CC BY-NC-SA 4.0** —
attribution required, no commercial use without separate authorisation, and
derivatives under the same terms.

When reusing a dataset, cite it. `citation_apa()` and `citation_bibtex()`
produce a correctly formatted reference.

## Citing

Datasets: use the citation returned by the client.

The repository itself is described in a white paper with a DOI:

> Xavier, J. (2026). *GPRBase: A Free Library of Real-World Ground Penetrating
> Radar Datasets for Education, Training and Research.*
> https://doi.org/10.5281/zenodo.21894933

## Contributing

Issues and pull requests welcome. If you hold GPR acquisitions that could serve
teaching or research, GPRbase accepts dataset contributions with full credit to
the contributor — see the contribution page on the site.

## Related

- [GPRbase](https://www.gprbase.com) — the dataset catalogue
- [GPRviewer](https://www.gprviewer.com) — browser-based DZT viewer
- [readgssi](https://github.com/iannesbitt/readgssi), [GPRPy](https://github.com/NSGeophysics/GPRPy), [RGPR](https://github.com/emanuelhuber/RGPR) — open-source DZT readers these datasets work with

---

# Client API GPRbase (français)

Accès programmatique à [GPRbase](https://www.gprbase.com) — une bibliothèque
libre de **données géoradar réelles** acquises avec du matériel GSSI, couvrant
le béton armé, les réseaux enterrés, la géotechnique, les chaussées,
l'archéologie et les géosciences.

Fichiers `.DZT` bruts, non traités, sous licence CC BY-NC-SA 4.0.

Clients Python et JavaScript, sans aucune dépendance.

## Pourquoi

La théorie du géoradar s'enseigne dans un livre ; l'interprétation, non. Elle
s'acquiert en travaillant sur de nombreux radargrammes réels — et les données de
terrain manquent cruellement aux formateurs, aux étudiants et aux développeurs.

GPRbase publie ces données. Ce client rend le catalogue exploitable depuis un
script : filtrer par application, antenne ou fréquence, récupérer les
métadonnées, produire des citations, exporter en CSV.

## Installation

Rien à installer. Copiez le fichier dont vous avez besoin.

```bash
curl -O https://raw.githubusercontent.com/MDS-GPRbase/gprbase-api-client/main/python/gprbase.py
curl -O https://raw.githubusercontent.com/MDS-GPRbase/gprbase-api-client/main/javascript/gprbase.js
```

## Exemple

```python
from gprbase import GPRbase

gpr = GPRbase()

# Datasets béton acquis avec une antenne FLEX NX
for d in gpr.datasets(application="beton", antenna="FLEX NX"):
    print(d.id, d.title_in("fr"), d.url_fr)

# Tout ce qui a été acquis à 300 MHz
gpr.datasets(frequency="300")

# Recherche plein texte, insensible aux accents
gpr.datasets(search="voute")

# Un dataset et sa citation
ds = gpr.dataset("ds016")
print(ds.citation_apa())
```

En ligne de commande :

```bash
python gprbase.py list --application reseaux --lang fr
python gprbase.py show ds016
python gprbase.py stats
```

## Filtres

Le filtre `application` accepte indifféremment `beton`, `Béton` ou `concrete`.
Les champs multivalués sont découpés automatiquement : une antenne
`FLEX NX;NX25;NX15` devient une liste de trois, une fréquence `300/800` devient
`["300", "800"]`.

## Licences

Le client est sous **MIT**. Les données auxquelles il donne accès sont sous
**CC BY-NC-SA 4.0** : attribution obligatoire, pas d'usage commercial sans
autorisation distincte, partage à l'identique.

Lors de la réutilisation d'un dataset, citez-le. `citation_apa()` et
`citation_bibtex()` produisent une référence correctement formée.

## Contribuer

Les tickets et propositions de modification sont bienvenus. Si vous disposez
d'acquisitions géoradar utiles à la formation ou à la recherche, GPRbase accepte
les contributions de jeux de données, avec crédit au contributeur.
