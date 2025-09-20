const API_URL = process.env.REACT_APP_API_URL;

const FACETS_CACHE = new Map();
const FACETS_TTL_MS = 60_000;

const facetsKey = (params = {}) => {
  const { department, team, dateFrom, dateTo, eventTypes } = params;
  const types =
    Array.isArray(eventTypes) && eventTypes.length && !eventTypes.includes('all')
      ? eventTypes.slice().sort().join(',')
      : '';
  return JSON.stringify({ department, team, dateFrom, dateTo, types });
};

const authHeaders = () => {
  const token = localStorage.getItem('access_token');
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  };
};

export async function fetchBehaviorLogs(params = {}) {
  const headers = authHeaders();
  const qs = new URLSearchParams();

  const {
    limit,
    department,
    team,
    user,
    sortKey,
    sortOrder,
    eventTypes,
    dateFrom,
    dateTo,
    cursor,
    offset,
    includeTotal,
  } = params;

  if (limit != null) qs.set('limit', limit);
  if (department) qs.set('department', department);
  if (team) qs.set('team', team);
  if (user) qs.set('user', user);
  if (sortKey) qs.set('sort_by', sortKey);
  if (sortOrder) qs.set('sort_order', sortOrder);
  if (Array.isArray(eventTypes) && eventTypes.length && !eventTypes.includes('all')) {
    qs.set('event_types', eventTypes.join(','));
  }
  if (dateFrom) qs.set('date_from', dateFrom);
  if (dateTo) qs.set('date_to', dateTo);
  if (includeTotal) qs.set('include_total', '1');

  if (cursor && cursor.after_ts && cursor.after_id) {
    qs.set('after_ts', cursor.after_ts);
    qs.set('after_id', cursor.after_id);
  } else if (offset != null) {
    qs.set('offset', offset);
  }

  try {
    const res = await fetch(`${API_URL}/behavior-logs?${qs.toString()}`, { headers });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    let json = {};
    try {
      json = await res.json();
    } catch {
      json = {};
    }

    const items = Array.isArray(json.items)
      ? json.items
      : Array.isArray(json.data)
      ? json.data
      : [];
    const total = Number.isFinite(json.total) ? json.total : null;
    const hasMore = Boolean(json.has_more);
    const nextCursor =
      json.next_cursor && json.next_cursor.after_id ? json.next_cursor : null;

    return { items, total, hasMore, nextCursor };
  } catch (e) {
    console.warn('[BehaviorLogsService] fetchBehaviorLogs 실패', e);
    return { items: [], total: null, hasMore: false, nextCursor: null };
  }
}

export async function fetchBehaviorFacets(params = {}) {
  const headers = authHeaders();
  const key = facetsKey(params);
  const now = Date.now();

  const hit = FACETS_CACHE.get(key);
  if (hit && now - hit.t < FACETS_TTL_MS) return hit.v;

  const qs = new URLSearchParams();
  const { department, team, dateFrom, dateTo, eventTypes } = params;

  if (department) qs.set('department', department);
  if (team) qs.set('team', team);
  if (dateFrom) qs.set('date_from', dateFrom);
  if (dateTo) qs.set('date_to', dateTo);
  if (Array.isArray(eventTypes) && eventTypes.length && !eventTypes.includes('all')) {
    qs.set('event_types', eventTypes.join(','));
  }

  try {
    const res = await fetch(`${API_URL}/behavior-logs/facets?${qs.toString()}`, {
      headers,
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const json = await res.json();

    const out = {
      departments: Array.isArray(json.departments) ? json.departments : [],
      teams: Array.isArray(json.teams) ? json.teams : [],
      employees: Array.isArray(json.employees) ? json.employees : [],
    };

    FACETS_CACHE.set(key, { v: out, t: now });
    return out;
  } catch (e) {
    console.warn('[BehaviorLogsService] fetchBehaviorFacets 실패', e);
    return { departments: [], teams: [], employees: [] };
  }
}