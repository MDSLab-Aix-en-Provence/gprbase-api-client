"""Short tour of the GPRbase API client."""

from gprbase import GPRbase, APPLICATIONS

gpr = GPRbase()

# 1. How big is the catalogue?
catalog = gpr.catalog()
print(f"{catalog['countPublic']} public datasets, updated {catalog['generatedAt']}\n")

# 2. Concrete datasets recorded with a FLEX NX antenna
for d in gpr.datasets(application="beton", antenna="FLEX NX"):
    print(f"{d.id}  {d.title}")
    print(f"        {d.antenna} · {d.frequency_mhz} MHz · {d.url}")

# 3. Anything acquired at 300 MHz, whichever the application
print("\n300 MHz datasets:")
for d in gpr.datasets(frequency="300"):
    print(f"  {d.id}  {', '.join(d.applications)}")

# 4. Full-text search, accent-insensitive
print("\nSearch 'voute':")
for d in gpr.datasets(search="voute"):
    print(f"  {d.id}  {d.title}")

# 5. Datasets whose targets were confirmed independently of the radar
print("\nGround truth verified:")
for d in gpr.datasets(ground_truth="verified"):
    print(f"  {d.id}  {d.title}")
    print(f"        method: {d.ground_truth_method or 'not stated'}")

print("\nGround truth across the catalogue:")
for level, n in gpr.ground_truth_summary().items():
    print(f"  {n:3d}  {level}")

# 6. One dataset, with its citation
ds = gpr.dataset("ds016")
print(f"\n{ds.title}\n")
print(ds.citation_apa())

# 7. Catalogue overview
print("\nDatasets per application:")
for key, n in gpr.applications().items():
    print(f"  {n:3d}  {APPLICATIONS.get(key, key)}")

# 8. Export
with open("gprbase-datasets.csv", "w", newline="", encoding="utf-8") as handle:
    gpr.to_csv(handle)
print("\nWritten: gprbase-datasets.csv")
