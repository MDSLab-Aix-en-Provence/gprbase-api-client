/**
 * GPRbase API client — access the free GPR dataset catalogue from JavaScript.
 *
 * GPRbase (https://www.gprbase.com) publishes real-world Ground Penetrating
 * Radar field data recorded with GSSI equipment, under CC BY-NC-SA 4.0.
 *
 * Works in the browser and in Node 18+. No dependencies.
 *
 * @example
 *   import { GPRbase } from './gprbase.js';
 *
 *   const gpr = new GPRbase();
 *   const concrete = await gpr.datasets({ application: 'beton' });
 *   const validated = await gpr.datasets({ groundTruth: 'verified' });
 *   concrete.forEach(d => console.log(d.id, d.title));
 *
 * Licence: MIT. The client is MIT; the datasets are CC BY-NC-SA 4.0.
 */

export const VERSION = '1.1.0';
const DEFAULT_BASE_URL = 'https://www.gprbase.com';

/** Canonical application keys used by the catalogue. */
export const APPLICATIONS = {
  beton: 'Reinforced concrete / Civil engineering',
  reseaux: 'Underground utilities',
  geotech: 'Geotechnical investigation',
  archeologie: 'Archaeology and built heritage',
  routes: 'Roads and pavements',
  geosciences: 'Geosciences',
};

const ALIASES = {
  concrete: 'beton', civilengineering: 'beton',
  utilities: 'reseaux', undergroundutilities: 'reseaux', reseauxenterres: 'reseaux',
  geotechnical: 'geotech', geotechnique: 'geotech',
  archaeology: 'archeologie', archeology: 'archeologie', heritage: 'archeologie',
  roads: 'routes', roadspavements: 'routes',
  geoscience: 'geosciences',
};

/** Lowercase, strip accents and punctuation — used for tolerant matching. */
function norm(value) {
  return String(value ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]/g, '');
}

export class GPRbaseError extends Error {
  constructor(message) {
    super(message);
    this.name = 'GPRbaseError';
  }
}

/** One GPR dataset, as described by the catalogue. */
export class Dataset {
  constructor(payload) {
    this.raw = payload;
    this.id = payload.id ?? '';
    this.title = payload.title ?? '';
    this.titleFr = payload.title_fr ?? '';
    this.description = payload.description ?? '';
    this.descriptionFr = payload.description_fr ?? '';
    this.applications = payload.applications ?? [];
    this.antenna = payload.antenna ?? '';
    this.frequencyMhz = String(payload.frequency_mhz ?? '');
    this.manufacturer = payload.manufacturer ?? 'GSSI';
    this.format = payload.format ?? 'DZT';
    this.dataType = payload.dataType ?? 'raw';
    this.fileCount = payload.fileCount ?? null;
    this.targets = payload.targets ?? [];
    this.contributor = payload.contributor ?? '';
    this.datePublished = payload.datePublished ?? null;
    this.license = payload.license ?? '';
    this.status = payload.status ?? 'public';
    this.channels = payload.channels ?? null;
    this.gpsAvailable = payload.gpsAvailable ?? null;
    this.groundTruth = payload.groundTruth ?? 'none';
    this.groundTruthMethod = payload.groundTruthMethod ?? null;
    this.isAccessibleForFree = payload.isAccessibleForFree !== false;
    this.isAccessibleForPro = payload.isAccessibleForPro === true;
    this.url = payload.url ?? null;
    this.urlFr = payload.url_fr ?? null;
    this.publisher = payload.publisher ?? 'GPRbase';
  }

  /** Frequencies as an array. '300/800' and '2500;1500' both split. */
  get frequencies() {
    return this.frequencyMhz.replace(/;/g, '/').split('/')
      .map(s => s.trim()).filter(Boolean);
  }

  /** Antennas as an array — a dataset may combine several. */
  get antennas() {
    return this.antenna.split(';').map(s => s.trim()).filter(Boolean);
  }

  /** La cible a-t-elle ete confirmee par un moyen independant du radar ? */
  get isVerified() {
    return this.groundTruth === 'verified';
  }

  /** Les fichiers .DZG sont-ils inclus ? false si inconnu. */
  get isGeoreferenced() {
    return this.gpsAvailable === true;
  }

  get year() {
    return this.datePublished ? this.datePublished.slice(0, 4) : null;
  }

  /** Tolerant to case, accents and the French/English label. */
  hasApplication(application) {
    let target = norm(application);
    target = ALIASES[target] ?? target;
    return this.applications.some(a => norm(a) === target);
  }

  titleIn(lang = 'en') {
    return lang === 'fr' ? (this.titleFr || this.title) : (this.title || this.titleFr);
  }

  descriptionIn(lang = 'en') {
    return lang === 'fr'
      ? (this.descriptionFr || this.description)
      : (this.description || this.descriptionFr);
  }

  urlIn(lang = 'en') {
    return lang === 'fr' ? this.urlFr : this.url;
  }

  _equipment() {
    const bits = [this.manufacturer, this.antenna];
    if (this.frequencyMhz) bits.push(`${this.frequencyMhz} MHz`);
    return bits.filter(Boolean).join(', ');
  }

  /** APA-style citation. Author is the publishing organisation. */
  citationApa() {
    const author = 'MDS - Le Matériel de Sondage - GPRbase';
    let out = `${author} (${this.year ?? 'n.d.'}). ${this.title} [Data set]. GPRbase.`;
    const equip = this._equipment();
    if (equip) out += ` ${equip}.`;
    const internal = ['mds', 'mdslab', 'gprbase'];
    if (this.contributor && !internal.includes(this.contributor.toLowerCase())) {
      out += ` Data acquired by ${this.contributor}.`;
    }
    if (this.url) out += ` ${this.url}`;
    return out;
  }

  citationBibtex() {
    const key = norm(this.id);
    const note = [this._equipment(), 'Licensed under CC BY-NC-SA 4.0']
      .filter(Boolean).join('. ');
    return [
      `@misc{gprbase_${key},`,
      `  author       = {MDS - Le Matériel de Sondage - GPRbase},`,
      `  title        = {${this.title}},`,
      `  year         = {${this.year ?? 'n.d.'}},`,
      `  publisher    = {GPRbase},`,
      `  howpublished = {\\url{${this.url ?? ''}}},`,
      `  note         = {${note}},`,
      `}`,
    ].join('\n');
  }

  toString() {
    return `${this.id} — ${this.title}`;
  }
}

/** Read-only client for the public GPRbase catalogue. */
export class GPRbase {
  /**
   * @param {object} [options]
   * @param {string} [options.baseUrl] catalogue host
   * @param {string} [options.token]   optional access token
   */
  constructor({ baseUrl = DEFAULT_BASE_URL, token = null } = {}) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.token = token;
    this._catalog = null;
  }

  async _get(path) {
    let url = `${this.baseUrl}${path}`;
    if (this.token) url += (url.includes('?') ? '&' : '?') + `token=${encodeURIComponent(this.token)}`;
    let response;
    try {
      response = await fetch(url, { headers: { Accept: 'application/json' } });
    } catch (cause) {
      throw new GPRbaseError(`Cannot reach ${url}: ${cause.message}`);
    }
    if (!response.ok) throw new GPRbaseError(`HTTP ${response.status} for ${url}`);
    try {
      return await response.json();
    } catch {
      throw new GPRbaseError(`Invalid JSON from ${url}`);
    }
  }

  /** Full catalogue payload, including count and generatedAt. */
  async catalog({ refresh = false } = {}) {
    if (!this._catalog || refresh) {
      this._catalog = await this._get('/api/datasets.json');
    }
    return this._catalog;
  }

  /** Use a saved copy of the catalogue — handy offline or in tests. */
  loadFromObject(payload) {
    this._catalog = payload;
    return this._catalog;
  }

  /**
   * Datasets matching every filter given. Omitted filters are ignored.
   * @param {object} [filters]
   * @param {string} [filters.application]
   * @param {string} [filters.antenna]
   * @param {string} [filters.frequency]
   * @param {string} [filters.contributor]
   * @param {string} [filters.search]
   * @param {boolean} [filters.freeOnly=true]
   * @returns {Promise<Dataset[]>}
   */
  async datasets({
    application, antenna, frequency, contributor, search,
    groundTruth, gps, minChannels, freeOnly = true,
  } = {}) {
    const catalog = await this.catalog();
    let items = (catalog.datasets ?? []).map(d => new Dataset(d));

    if (freeOnly) items = items.filter(d => d.isAccessibleForFree);
    if (application) items = items.filter(d => d.hasApplication(application));
    if (antenna) {
      const needle = norm(antenna);
      items = items.filter(d => d.antennas.some(a => norm(a).includes(needle)));
    }
    if (frequency) {
      const needle = String(frequency).trim();
      items = items.filter(d => d.frequencies.includes(needle));
    }
    if (contributor) {
      const needle = norm(contributor);
      items = items.filter(d => norm(d.contributor).includes(needle));
    }
    if (groundTruth) {
      let wanted = norm(groundTruth);
      wanted = ({ yes: 'verified', confirmed: 'verified', true: 'verified' })[wanted] ?? wanted;
      items = items.filter(d => norm(d.groundTruth) === wanted);
    }
    if (gps !== undefined && gps !== null) {
      items = items.filter(d => d.gpsAvailable === gps);
    }
    if (minChannels) {
      items = items.filter(d => (d.channels ?? 0) >= minChannels);
    }
    if (search) {
      const needle = norm(search);
      items = items.filter(d => norm([
        d.title, d.titleFr, d.description, d.descriptionFr,
        d.antenna, d.targets.join(' '),
      ].join(' ')).includes(needle));
    }
    return items;
  }

  /**
   * One dataset by identifier, fetched from its own endpoint.
   * That endpoint also returns ready-made citations.
   */
  async dataset(id) {
    const payload = await this._get(`/api/datasets/${encodeURIComponent(id)}.json`);
    if (payload.error) throw new GPRbaseError(`Dataset ${id} not found or not public`);
    return new Dataset(payload);
  }

  /** How many datasets per application key. */
  async applications() {
    const counts = {};
    for (const d of await this.datasets()) {
      for (const app of d.applications) counts[app] = (counts[app] ?? 0) + 1;
    }
    return Object.fromEntries(Object.entries(counts).sort((a, b) => b[1] - a[1]));
  }

  /** How many datasets per ground truth level. */
  async groundTruthSummary() {
    const counts = { verified: 0, partial: 0, none: 0 };
    for (const d of await this.datasets()) {
      counts[d.groundTruth] = (counts[d.groundTruth] ?? 0) + 1;
    }
    return counts;
  }

  /** How many datasets per antenna. */
  async antennas() {
    const counts = {};
    for (const d of await this.datasets()) {
      for (const a of d.antennas) counts[a] = (counts[a] ?? 0) + 1;
    }
    return Object.fromEntries(Object.entries(counts).sort((a, b) => b[1] - a[1]));
  }
}

export default GPRbase;
