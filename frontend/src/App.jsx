import { useEffect, useMemo, useState } from 'react'
import './App.css'
import { apiBaseUrl, apiRequest } from './api'

const STATUS_OPTIONS = [
  { value: 'wishlist', label: 'Wishlist' },
  { value: 'playing', label: 'Playing' },
  { value: 'completed', label: 'Completed' },
  { value: 'dropped', label: 'Dropped' },
]

const STATUS_LABELS = Object.fromEntries(
  STATUS_OPTIONS.map((option) => [option.value, option.label]),
)

const initialAuthForm = { username: '', password: '', email: '' }

function buildEditDrafts(entries) {
  const next = {}
  for (const entry of entries) {
    next[entry.id] = {
      status: entry.status,
      hours_played: String(entry.hours_played),
    }
  }
  return next
}

function getErrorMessage(error, fallback) {
  if (!error) return fallback
  if (error.data?.details) {
    const detailText = Object.entries(error.data.details)
      .map(([field, message]) => `${field}: ${message}`)
      .join(' | ')
    if (detailText) return detailText
  }
  if (typeof error.message === 'string' && error.message.trim()) return error.message
  return fallback
}

function toInt(value) {
  const parsed = Number.parseInt(value, 10)
  return Number.isNaN(parsed) ? null : parsed
}

function App() {
  const [sessionState, setSessionState] = useState('loading')
  const [user, setUser] = useState(null)
  const [entries, setEntries] = useState([])
  const [selectedEntryId, setSelectedEntryId] = useState(null)
  const [selectedEntry, setSelectedEntry] = useState(null)

  const [authMode, setAuthMode] = useState('login')
  const [authForm, setAuthForm] = useState(initialAuthForm)
  const [authLoading, setAuthLoading] = useState(false)
  const [authError, setAuthError] = useState('')

  const [entriesLoading, setEntriesLoading] = useState(false)
  const [entriesError, setEntriesError] = useState('')

  const [createLoading, setCreateLoading] = useState(false)

  const [editDrafts, setEditDrafts] = useState({})
  const [updateLoadingId, setUpdateLoadingId] = useState(null)

  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')

  // --- Catálogo (Ejercicios 2-5) ---
  const [catalogQuery, setCatalogQuery] = useState('')
  const [catalogResults, setCatalogResults] = useState([])
  const [catalogLoading, setCatalogLoading] = useState(false)
  const [catalogError, setCatalogError] = useState('')
  const [addingGameId, setAddingGameId] = useState(null)
  const [addStatus, setAddStatus] = useState('wishlist')

  // Info enriquecida del catálogo (resolve)
  const [resolvedGames, setResolvedGames] = useState({})

  // --- Pestaña activa ---
  const [activeTab, setActiveTab] = useState('catalog')

  // --- Bootstrap session ---
  useEffect(() => {
    async function runBootstrapSession() {
      setSessionState('loading')
      setEntriesError('')
      try {
        const me = await apiRequest('/api/users/me/')
        const data = await apiRequest('/api/library/entries/')
        setUser(me)
        setEntries(Array.isArray(data) ? data : [])
        setEditDrafts(buildEditDrafts(Array.isArray(data) ? data : []))
        setSessionState('authenticated')
      } catch (error) {
        if (error.status === 401) {
          setUser(null)
          setSessionState('anonymous')
          setEntries([])
          return
        }
        setSessionState('anonymous')
        setEntries([])
        setEntriesError(getErrorMessage(error, 'No se pudo validar la sesion con el backend.'))
      }
    }
    runBootstrapSession()
  }, [])

  // --- Detalle entrada ---
  useEffect(() => {
    if (!selectedEntryId) return
    async function runLoadEntryDetail() {
      try {
        const detail = await apiRequest(`/api/library/entries/${selectedEntryId}/`)
        setSelectedEntry(detail)
      } catch (error) {
        setSelectedEntry(null)
        if (error.status !== 404) {
          setEntriesError(getErrorMessage(error, 'No se pudo cargar el detalle de la entrada.'))
        }
      }
    }
    runLoadEntryDetail()
  }, [selectedEntryId])

  // --- Resolve: enriquecer biblioteca con título y thumb ---
  // Resolver cuando cambian las entries
  useEffect(() => {
    const ids = entries.map((e) => e.external_game_id).filter(Boolean)
    if (ids.length === 0) {
      return undefined
    }

    let cancelled = false
    async function runResolveLibraryGames() {
      try {
        const resolved = await apiRequest('/api/catalog/resolve/', {
          method: 'POST',
          body: { external_game_ids: ids },
        })
        if (cancelled) return
        const map = {}
        for (const game of resolved) {
          map[game.external_game_id] = game
        }
        setResolvedGames(map)
      } catch {
        // No bloquear si falla resolve.
      }
    }

    runResolveLibraryGames()
    return () => { cancelled = true }
  }, [entries])

  const filteredEntries = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase()
    return entries.filter((entry) => {
      const matchesStatus = statusFilter === 'all' || entry.status === statusFilter
      const resolved = resolvedGames[entry.external_game_id]
      const title = resolved?.title || ''
      const matchesSearch =
        normalizedSearch === '' ||
        entry.external_game_id.toLowerCase().includes(normalizedSearch) ||
        title.toLowerCase().includes(normalizedSearch)
      return matchesStatus && matchesSearch
    })
  }, [entries, searchTerm, statusFilter, resolvedGames])

  const summary = useMemo(() => {
    const counts = { wishlist: 0, playing: 0, completed: 0, dropped: 0 }
    let totalHours = 0
    for (const entry of entries) {
      if (counts[entry.status] !== undefined) counts[entry.status] += 1
      totalHours += entry.hours_played
    }
    return { totalEntries: entries.length, totalHours, counts }
  }, [entries])

  async function loadEntries() {
    setEntriesLoading(true)
    setEntriesError('')
    try {
      const data = await apiRequest('/api/library/entries/')
      const normalizedEntries = Array.isArray(data) ? data : []
      setEntries(normalizedEntries)
      setEditDrafts(buildEditDrafts(normalizedEntries))
      if (selectedEntryId) {
        const stillExists = normalizedEntries.some((e) => e.id === selectedEntryId)
        if (!stillExists) { setSelectedEntryId(null); setSelectedEntry(null) }
      }
    } catch (error) {
      setEntriesError(getErrorMessage(error, 'No se pudo cargar la biblioteca.'))
    } finally {
      setEntriesLoading(false)
    }
  }

  // --- Auth ---
  async function handleAuthSubmit(event) {
    event.preventDefault()
    setAuthLoading(true)
    setAuthError('')
    try {
      const credentials = { username: authForm.username, password: authForm.password }
      if (authMode === 'register') {
        await apiRequest('/api/auth/register/', {
          method: 'POST',
          body: { ...credentials, email: authForm.email },
        })
      }
      const loginResponse = await apiRequest('/api/auth/login/', { method: 'POST', body: credentials })
      setUser(loginResponse)
      setAuthForm(initialAuthForm)
      setSessionState('authenticated')
      await loadEntries()
    } catch (error) {
      setAuthError(getErrorMessage(error, 'No se pudo iniciar sesion con las credenciales enviadas.'))
    } finally {
      setAuthLoading(false)
    }
  }

  async function handleLogout() {
    try { await apiRequest('/api/auth/logout/', { method: 'POST' }) } catch {
      // La sesion puede estar expirada igualmente.
    }
    setUser(null); setEntries([]); setSelectedEntry(null); setSelectedEntryId(null)
    setSessionState('anonymous'); setAuthMode('login'); setResolvedGames({})
  }

  // --- Catálogo: buscar (Ejercicio 2) ---
  async function handleCatalogSearch(event) {
    event.preventDefault()
    const q = catalogQuery.trim()
    if (!q) { setCatalogError('Escribe un término de búsqueda.'); return }
    setCatalogLoading(true)
    setCatalogError('')
    setCatalogResults([])
    try {
      const results = await apiRequest(`/api/catalog/search/?q=${encodeURIComponent(q)}`)
      setCatalogResults(Array.isArray(results) ? results : [])
      if (Array.isArray(results) && results.length === 0) {
        setCatalogError('No se encontraron resultados.')
      }
    } catch (error) {
      setCatalogError(getErrorMessage(error, 'Error al buscar en el catálogo.'))
    } finally {
      setCatalogLoading(false)
    }
  }

  // --- Añadir juego desde catálogo (Ejercicio 5 flujo) ---
  async function handleAddFromCatalog(game) {
    setAddingGameId(game.external_game_id)
    setEntriesError('')
    setCatalogError('')
    try {
      const created = await apiRequest('/api/library/entries/', {
        method: 'POST',
        body: {
          external_game_id: game.external_game_id,
          status: addStatus,
          hours_played: 0,
        },
      })
      setEntries((current) => [...current, created])
      setEditDrafts((current) => ({
        ...current,
        [created.id]: { status: created.status, hours_played: String(created.hours_played) },
      }))
      setActiveTab('library')
    } catch (error) {
      setCatalogError(getErrorMessage(error, 'No se pudo añadir el juego.'))
    } finally {
      setAddingGameId(null)
    }
  }

  // --- Crear entrada manual ---
  const [manualForm, setManualForm] = useState({ external_game_id: '', status: 'wishlist', hours_played: '0' })

  async function handleCreateEntry(event) {
    event.preventDefault()
    const hours = toInt(manualForm.hours_played)
    if (hours === null || hours < 0) { setEntriesError('hours_played debe ser >= 0.'); return }
    setCreateLoading(true)
    setEntriesError('')
    try {
      const created = await apiRequest('/api/library/entries/', {
        method: 'POST',
        body: { external_game_id: manualForm.external_game_id.trim(), status: manualForm.status, hours_played: hours },
      })
      setEntries((current) => [...current, created])
      setEditDrafts((current) => ({
        ...current,
        [created.id]: { status: created.status, hours_played: String(created.hours_played) },
      }))
      setManualForm({ external_game_id: '', status: 'wishlist', hours_played: '0' })
      setSelectedEntryId(created.id)
    } catch (error) {
      setEntriesError(getErrorMessage(error, 'No se pudo crear la entrada.'))
    } finally {
      setCreateLoading(false)
    }
  }

  function handleDraftChange(entryId, field, value) {
    setEditDrafts((current) => ({ ...current, [entryId]: { ...current[entryId], [field]: value } }))
  }

  async function handleUpdateEntry(entryId) {
    const draft = editDrafts[entryId]
    if (!draft) return
    const hours = toInt(draft.hours_played)
    if (hours === null || hours < 0) { setEntriesError('hours_played debe ser >= 0.'); return }
    setUpdateLoadingId(entryId)
    setEntriesError('')
    try {
      const updated = await apiRequest(`/api/library/entries/${entryId}/`, {
        method: 'PATCH',
        body: { status: draft.status, hours_played: hours },
      })
      setEntries((current) => current.map((e) => (e.id === entryId ? updated : e)))
      setEditDrafts((current) => ({
        ...current,
        [entryId]: { status: updated.status, hours_played: String(updated.hours_played) },
      }))
      if (selectedEntryId === entryId) setSelectedEntry(updated)
    } catch (error) {
      setEntriesError(getErrorMessage(error, 'No se pudo actualizar la entrada.'))
    } finally {
      setUpdateLoadingId(null)
    }
  }

  // ===== RENDER =====

  if (sessionState === 'loading') {
    return (
      <div className="screen-center">
        <div className="loader-panel">
          <h1>Nexus Play</h1>
          <p>Conectando con backend...</p>
        </div>
      </div>
    )
  }

  if (sessionState === 'anonymous') {
    return (
      <div className="auth-screen">
        <section className="auth-hero">
          <p className="eyebrow">Steam-like frontend</p>
          <h1>Nexus Play Console</h1>
          <p>Interfaz conectada a tus views de Django para autenticacion por sesion y gestion de biblioteca.</p>
          <ul>
            <li>GET /api/catalog/search/?q=...</li>
            <li>POST /api/catalog/resolve/</li>
            <li>GET/POST/PATCH /api/library/entries/</li>
          </ul>
        </section>
        <section className="auth-form-panel">
          <div className="auth-mode-toggle">
            <button type="button" className={authMode === 'login' ? 'active' : ''} onClick={() => { setAuthMode('login'); setAuthError('') }}>Login</button>
            <button type="button" className={authMode === 'register' ? 'active' : ''} onClick={() => { setAuthMode('register'); setAuthError('') }}>Registro</button>
          </div>
          <form onSubmit={handleAuthSubmit} className="auth-form">
            <label htmlFor="username">Username
              <input id="username" name="username" autoComplete="username" value={authForm.username} onChange={(e) => setAuthForm((c) => ({ ...c, username: e.target.value }))} required />
            </label>
            <label htmlFor="password">Password
              <input id="password" name="password" type="password" autoComplete={authMode === 'login' ? 'current-password' : 'new-password'} value={authForm.password} onChange={(e) => setAuthForm((c) => ({ ...c, password: e.target.value }))} required />
            </label>
            {authMode === 'register' && (
              <label htmlFor="email">Email
                <input id="email" name="email" type="email" autoComplete="email" value={authForm.email} onChange={(e) => setAuthForm((c) => ({ ...c, email: e.target.value }))} required />
              </label>
            )}
            <button type="submit" disabled={authLoading}>{authLoading ? 'Procesando...' : authMode === 'login' ? 'Iniciar sesion' : 'Crear cuenta y entrar'}</button>
          </form>
          {authError && <p className="message message--error">{authError}</p>}
          {entriesError && <p className="message message--error">{entriesError}</p>}
          <p className="api-hint">API base: {apiBaseUrl}</p>
        </section>
      </div>
    )
  }

  // === AUTHENTICATED ===
  return (
    <div className="app-layout">
      <header className="topbar">
        <div>
          <p className="eyebrow">Library Dashboard</p>
          <h1>Nexus Play</h1>
          <p className="welcome">Sesion activa como <strong>{user?.username}</strong></p>
        </div>
        <div className="header-actions">
          <button type="button" onClick={loadEntries} disabled={entriesLoading}>{entriesLoading ? 'Actualizando...' : 'Actualizar'}</button>
          <button type="button" className="ghost" onClick={handleLogout}>Cerrar sesion</button>
        </div>
      </header>

      <section className="summary-strip">
        <article><span>Total entradas</span><strong>{summary.totalEntries}</strong></article>
        <article><span>Horas jugadas</span><strong>{summary.totalHours}</strong></article>
        <article><span>Playing</span><strong>{summary.counts.playing}</strong></article>
        <article><span>Completed</span><strong>{summary.counts.completed}</strong></article>
      </section>

      {/* Pestañas */}
      <div className="tab-bar">
        <button type="button" className={activeTab === 'catalog' ? 'tab active' : 'tab'} onClick={() => setActiveTab('catalog')}>🔍 Buscar en Catálogo</button>
        <button type="button" className={activeTab === 'library' ? 'tab active' : 'tab'} onClick={() => setActiveTab('library')}>📚 Mi Biblioteca</button>
        <button type="button" className={activeTab === 'manual' ? 'tab active' : 'tab'} onClick={() => setActiveTab('manual')}>➕ Entrada Manual</button>
      </div>

      <main className="workspace">
        <section className="workspace-main">

          {/* TAB: Catálogo (Ejercicio 2 + 5) */}
          {activeTab === 'catalog' && (
            <section className="catalog-panel">
              <h2>Buscar en Catálogo Externo</h2>
              <p className="catalog-hint">Busca videojuegos por nombre. El backend consulta CheapShark y te devuelve resultados filtrados.</p>
              <form className="catalog-search-form" onSubmit={handleCatalogSearch}>
                <input
                  placeholder="Ej: mario, zelda, batman..."
                  value={catalogQuery}
                  onChange={(e) => setCatalogQuery(e.target.value)}
                />
                <button type="submit" disabled={catalogLoading}>{catalogLoading ? 'Buscando...' : 'Buscar'}</button>
              </form>

              {catalogError && <p className="message message--error">{catalogError}</p>}

              {catalogResults.length > 0 && (
                <div className="catalog-results">
                  <div className="catalog-add-bar">
                    <label>Estado al añadir:
                      <select value={addStatus} onChange={(e) => setAddStatus(e.target.value)}>
                        {STATUS_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                      </select>
                    </label>
                  </div>
                  <div className="catalog-grid">
                    {catalogResults.map((game) => {
                      const alreadyInLibrary = entries.some((e) => e.external_game_id === game.external_game_id)
                      return (
                        <div className="catalog-card" key={game.external_game_id}>
                          <img src={game.thumb} alt={game.title} className="catalog-thumb" loading="lazy" />
                          <div className="catalog-card-info">
                            <strong className="catalog-card-title">{game.title}</strong>
                            <span className="catalog-card-id">ID: {game.external_game_id}</span>
                          </div>
                          <button
                            type="button"
                            className={alreadyInLibrary ? 'catalog-add-btn added' : 'catalog-add-btn'}
                            disabled={alreadyInLibrary || addingGameId === game.external_game_id}
                            onClick={() => handleAddFromCatalog(game)}
                          >
                            {addingGameId === game.external_game_id ? 'Añadiendo...' : alreadyInLibrary ? '✓ En biblioteca' : '+ Añadir'}
                          </button>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}
            </section>
          )}

          {/* TAB: Biblioteca (Ejercicio 3 + 5) */}
          {activeTab === 'library' && (
            <section className="entries-panel">
              <div className="entries-header">
                <h2>Mi Biblioteca</h2>
                <div className="entries-filters">
                  <input placeholder="Buscar por título o ID" value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} />
                  <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
                    <option value="all">Todos</option>
                    {STATUS_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                </div>
              </div>

              {entriesLoading && <p className="message">Cargando entradas...</p>}
              {entriesError && <p className="message message--error">{entriesError}</p>}
              {!entriesLoading && filteredEntries.length === 0 && <p className="message">No hay entradas para el filtro seleccionado.</p>}

              <div className="library-grid">
                {filteredEntries.map((entry) => {
                  const resolved = resolvedGames[entry.external_game_id]
                  const draft = editDrafts[entry.id] || { status: entry.status, hours_played: String(entry.hours_played) }
                  return (
                    <div className={`library-card ${selectedEntryId === entry.id ? 'library-card--selected' : ''}`} key={entry.id} onClick={() => { setSelectedEntry(null); setSelectedEntryId(entry.id) }}>
                      {resolved?.thumb && <img src={resolved.thumb} alt={resolved.title} className="library-card-thumb" loading="lazy" />}
                      <div className="library-card-body">
                        <strong className="library-card-title">{resolved?.title || entry.external_game_id}</strong>
                        <span className="library-card-id">ID: {entry.external_game_id}</span>
                        <div className="library-card-controls">
                          <select value={draft.status} onChange={(e) => { e.stopPropagation(); handleDraftChange(entry.id, 'status', e.target.value) }} onClick={(e) => e.stopPropagation()}>
                            {STATUS_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                          </select>
                          <input type="number" min="0" step="1" value={draft.hours_played} onChange={(e) => { e.stopPropagation(); handleDraftChange(entry.id, 'hours_played', e.target.value) }} onClick={(e) => e.stopPropagation()} />
                          <button type="button" disabled={updateLoadingId === entry.id} onClick={(e) => { e.stopPropagation(); handleUpdateEntry(entry.id) }}>
                            {updateLoadingId === entry.id ? '...' : 'Guardar'}
                          </button>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </section>
          )}

          {/* TAB: Entrada manual */}
          {activeTab === 'manual' && (
            <form className="entry-form" onSubmit={handleCreateEntry}>
              <h2>Nueva entrada manual</h2>
              {entriesError && <p className="message message--error">{entriesError}</p>}
              <div className="entry-form-grid">
                <label>external_game_id
                  <input value={manualForm.external_game_id} onChange={(e) => setManualForm((c) => ({ ...c, external_game_id: e.target.value }))} required />
                </label>
                <label>status
                  <select value={manualForm.status} onChange={(e) => setManualForm((c) => ({ ...c, status: e.target.value }))}>
                    {STATUS_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                </label>
                <label>hours_played
                  <input type="number" min="0" step="1" value={manualForm.hours_played} onChange={(e) => setManualForm((c) => ({ ...c, hours_played: e.target.value }))} required />
                </label>
              </div>
              <button type="submit" disabled={createLoading}>{createLoading ? 'Guardando...' : 'Crear entrada'}</button>
            </form>
          )}

        </section>

        <aside className="workspace-side">
          <section className="detail-panel">
            <h2>Detalle</h2>
            {!selectedEntryId || !selectedEntry ? (
              <p className="message">Selecciona una entrada de la biblioteca para ver su detalle.</p>
            ) : (
              <>
                {resolvedGames[selectedEntry.external_game_id]?.thumb && (
                  <img src={resolvedGames[selectedEntry.external_game_id].thumb} alt="" className="detail-thumb" />
                )}
                <dl>
                  <div><dt>ID</dt><dd>{selectedEntry.id}</dd></div>
                  <div><dt>Título</dt><dd>{resolvedGames[selectedEntry.external_game_id]?.title || '—'}</dd></div>
                  <div><dt>external_game_id</dt><dd>{selectedEntry.external_game_id}</dd></div>
                  <div><dt>status</dt><dd>{STATUS_LABELS[selectedEntry.status] || selectedEntry.status}</dd></div>
                  <div><dt>hours_played</dt><dd>{selectedEntry.hours_played}</dd></div>
                </dl>
              </>
            )}
          </section>

          <section className="detail-panel api-panel">
            <h2>Conexion API</h2>
            <ul>
              <li>Base URL: {apiBaseUrl}</li>
              <li>Cookies de sesion: activas</li>
              <li>CORS credentials: include</li>
              <li>Catálogo: CheapShark API</li>
            </ul>
          </section>
        </aside>
      </main>
    </div>
  )
}

export default App
