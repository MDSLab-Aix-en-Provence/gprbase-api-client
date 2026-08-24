/** Short tour of the GPRbase API client. */

import { GPRbase, APPLICATIONS } from './gprbase.js';

const gpr = new GPRbase();

// 1. How big is the catalogue?
const catalog = await gpr.catalog();
console.log(`${catalog.countPublic} public datasets, updated ${catalog.generatedAt}\n`);

// 2. Concrete datasets recorded with a FLEX NX antenna
for (const d of await gpr.datasets({ application: 'beton', antenna: 'FLEX NX' })) {
  console.log(`${d.id}  ${d.title}`);
  console.log(`        ${d.antenna} · ${d.frequencyMhz} MHz · ${d.url}`);
}

// 3. Anything acquired at 300 MHz, whichever the application
console.log('\n300 MHz datasets:');
for (const d of await gpr.datasets({ frequency: '300' })) {
  console.log(`  ${d.id}  ${d.applications.join(', ')}`);
}

// 4. Full-text search, accent-insensitive
console.log("\nSearch 'voute':");
for (const d of await gpr.datasets({ search: 'voute' })) {
  console.log(`  ${d.id}  ${d.title}`);
}

// 5. Datasets whose targets were confirmed independently of the radar
console.log('\nGround truth verified:');
for (const d of await gpr.datasets({ groundTruth: 'verified' })) {
  console.log(`  ${d.id}  ${d.title}`);
  console.log(`        method: ${d.groundTruthMethod ?? 'not stated'}`);
}
console.log('\nGround truth across the catalogue:', await gpr.groundTruthSummary());

// 6. One dataset, with its citation
const ds = await gpr.dataset('ds016');
console.log(`\n${ds.title}\n`);
console.log(ds.citationApa());

// 7. Catalogue overview
console.log('\nDatasets per application:');
for (const [key, n] of Object.entries(await gpr.applications())) {
  console.log(`  ${String(n).padStart(3)}  ${APPLICATIONS[key] ?? key}`);
}
