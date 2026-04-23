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

const initialAuthForm = {
  username: '',
  password: '',
}

const initialCreateForm = {
  external_game_id: '',
  status: 'wishlist',
  hours_played: '0',
}

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
  if (!error) {
    return fallback
  }

  if (error.data?.details) {
    const detailText = Object.entries(error.data.details)
      .map(([field, message]) => `${field}: ${message}`)
      .join(' | ')

    if (detailText) {
      return detailText
    }
  }

  if (typeof error.message === 'string' && error.message.trim()) {
    return error.message
  }

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

  const [createForm, setCreateForm] = useState(initialCreateForm)
  const [createLoading, setCreateLoading] = useState(false)

  const [editDrafts, setEditDrafts] = useState({})
  const [updateLoadingId, setUpdateLoadingId] = useState(null)

  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')

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

  useEffect(() => {
    if (!selectedEntryId) {
      return
    }

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

  const filteredEntries = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase()

    return entries.filter((entry) => {
      const matchesStatus = statusFilter === 'all' || entry.status === statusFilter
      const matchesSearch =
        normalizedSearch === '' ||
        entry.external_game_id.toLowerCase().includes(normalizedSearch)

      return matchesStatus && matchesSearch
    })
  }, [entries, searchTerm, statusFilter])

  const summary = useMemo(() => {
    const counts = {
      wishlist: 0,
      playing: 0,
      completed: 0,
      dropped: 0,
    }

    let totalHours = 0

    for (const entry of entries) {
      if (counts[entry.status] !== undefined) {
        counts[entry.status] += 1
      }
      totalHours += entry.hours_played
    }

    return {
      totalEntries: entries.length,
      totalHours,
      counts,
    }
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
        const stillExists = normalizedEntries.some((entry) => entry.id === selectedEntryId)

        if (!stillExists) {
          setSelectedEntryId(null)
          setSelectedEntry(null)
        }
      }
    } catch (error) {
      setEntriesError(getErrorMessage(error, 'No se pudo cargar la biblioteca.'))
    } finally {
      setEntriesLoading(false)
    }
  }

  async function handleAuthSubmit(event) {
    event.preventDefault()
    setAuthLoading(true)
    setAuthError('')

    try {
      if (authMode === 'register') {
        await apiRequest('/api/auth/register/', {
          method: 'POST',
          body: authForm,
        })
      }

      const loginResponse = await apiRequest('/api/auth/login/', {
        method: 'POST',
        body: authForm,
      })

      setUser(loginResponse)
      setAuthForm(initialAuthForm)
      setSessionState('authenticated')
      await loadEntries()
    } catch (error) {
      setAuthError(
        getErrorMessage(error, 'No se pudo iniciar sesion con las credenciales enviadas.'),
      )
    } finally {
      setAuthLoading(false)
    }
  }

  async function handleLogout() {
    try {
      await apiRequest('/api/auth/logout/', { method: 'POST' })
    } catch {
      // Ignore logout errors to ensure local session is cleaned.
    } finally {
      setUser(null)
      setEntries([])
      setSelectedEntry(null)
      setSelectedEntryId(null)
      setSessionState('anonymous')
      setAuthMode('login')
    }
  }

  async function handleCreateEntry(event) {
    event.preventDefault()

    const hours = toInt(createForm.hours_played)
    if (hours === null || hours < 0) {
      setEntriesError('hours_played debe ser un entero mayor o igual que 0.')
      return
    }

    setCreateLoading(true)
    setEntriesError('')

    try {
      const created = await apiRequest('/api/library/entries/', {
        method: 'POST',
        body: {
          external_game_id: createForm.external_game_id.trim(),
          status: createForm.status,
          hours_played: hours,
        },
      })

      setEntries((current) => [...current, created])
      setEditDrafts((current) => ({
        ...current,
        [created.id]: {
          status: created.status,
          hours_played: String(created.hours_played),
        },
      }))
      setCreateForm(initialCreateForm)
      setSelectedEntryId(created.id)
    } catch (error) {
      setEntriesError(getErrorMessage(error, 'No se pudo crear la entrada.'))
    } finally {
      setCreateLoading(false)
    }
  }

  function handleDraftChange(entryId, field, value) {
    setEditDrafts((current) => ({
      ...current,
      [entryId]: {
        ...current[entryId],
        [field]: value,
      },
    }))
  }

  async function handleUpdateEntry(entryId) {
    const draft = editDrafts[entryId]

    if (!draft) {
      return
    }

    const hours = toInt(draft.hours_played)
    if (hours === null || hours < 0) {
      setEntriesError('hours_played debe ser un entero mayor o igual que 0.')
      return
    }

    setUpdateLoadingId(entryId)
    setEntriesError('')

    try {
      const updated = await apiRequest(`/api/library/entries/${entryId}/`, {
        method: 'PATCH',
        body: {
          status: draft.status,
          hours_played: hours,
        },
      })

      setEntries((current) =>
        current.map((entry) => (entry.id === entryId ? updated : entry)),
      )

      setEditDrafts((current) => ({
        ...current,
        [entryId]: {
          status: updated.status,
          hours_played: String(updated.hours_played),
        },
      }))

      if (selectedEntryId === entryId) {
        setSelectedEntry(updated)
      }
    } catch (error) {
      setEntriesError(getErrorMessage(error, 'No se pudo actualizar la entrada.'))
    } finally {
      setUpdateLoadingId(null)
    }
  }

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
          <p>
            Interfaz conectada a tus views de Django para autenticacion por sesion y gestion
            de biblioteca.
          </p>
          <ul>
            <li>POST /api/auth/login/</li>
            <li>GET /api/users/me/</li>
            <li>GET/POST/PATCH /api/library/entries/</li>
          </ul>
        </section>

        <section className="auth-form-panel">
          <div className="auth-mode-toggle">
            <button
              type="button"
              className={authMode === 'login' ? 'active' : ''}
              onClick={() => {
                setAuthMode('login')
                setAuthError('')
              }}
            >
              Login
            </button>
            <button
              type="button"
              className={authMode === 'register' ? 'active' : ''}
              onClick={() => {
                setAuthMode('register')
                setAuthError('')
              }}
            >
              Registro
            </button>
          </div>

          <form onSubmit={handleAuthSubmit} className="auth-form">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              name="username"
              autoComplete="username"
              value={authForm.username}
              onChange={(event) =>
                setAuthForm((current) => ({
                  ...current,
                  username: event.target.value,
                }))
              }
              required
            />

            <label htmlFor="password">Password</label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete={authMode === 'login' ? 'current-password' : 'new-password'}
              value={authForm.password}
              onChange={(event) =>
                setAuthForm((current) => ({
                  ...current,
                  password: event.target.value,
                }))
              }
              required
            />

            <button type="submit" disabled={authLoading}>
              {authLoading
                ? 'Procesando...'
                : authMode === 'login'
                  ? 'Iniciar sesion'
                  : 'Crear cuenta y entrar'}
            </button>
          </form>

          {authError && <p className="message message--error">{authError}</p>}
          {entriesError && <p className="message message--error">{entriesError}</p>}
          <p className="api-hint">API base: {apiBaseUrl}</p>
        </section>
      </div>
    )
  }

  return (
    <div className="app-layout">
      <header className="topbar">
        <div>
          <p className="eyebrow">Library Dashboard</p>
          <h1>Nexus Play</h1>
          <p className="welcome">
            Sesion activa como <strong>{user?.username}</strong>
          </p>
        </div>

        <div className="header-actions">
          <button type="button" onClick={loadEntries} disabled={entriesLoading}>
            {entriesLoading ? 'Actualizando...' : 'Actualizar'}
          </button>
          <button type="button" className="ghost" onClick={handleLogout}>
            Cerrar sesion
          </button>
        </div>
      </header>

      <section className="summary-strip">
        <article>
          <span>Total entradas</span>
          <strong>{summary.totalEntries}</strong>
        </article>
        <article>
          <span>Horas jugadas</span>
          <strong>{summary.totalHours}</strong>
        </article>
        <article>
          <span>Playing</span>
          <strong>{summary.counts.playing}</strong>
        </article>
        <article>
          <span>Completed</span>
          <strong>{summary.counts.completed}</strong>
        </article>
      </section>

      <main className="workspace">
        <section className="workspace-main">
          <form className="entry-form" onSubmit={handleCreateEntry}>
            <h2>Nueva entrada</h2>
            <div className="entry-form-grid">
              <label>
                external_game_id
                <input
                  value={createForm.external_game_id}
                  onChange={(event) =>
                    setCreateForm((current) => ({
                      ...current,
                      external_game_id: event.target.value,
                    }))
                  }
                  required
                />
              </label>

              <label>
                status
                <select
                  value={createForm.status}
                  onChange={(event) =>
                    setCreateForm((current) => ({
                      ...current,
                      status: event.target.value,
                    }))
                  }
                >
                  {STATUS_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                hours_played
                <input
                  type="number"
                  min="0"
                  step="1"
                  value={createForm.hours_played}
                  onChange={(event) =>
                    setCreateForm((current) => ({
                      ...current,
                      hours_played: event.target.value,
                    }))
                  }
                  required
                />
              </label>
            </div>

            <button type="submit" disabled={createLoading}>
              {createLoading ? 'Guardando...' : 'Crear entrada'}
            </button>
          </form>

          <section className="entries-panel">
            <div className="entries-header">
              <h2>Biblioteca real</h2>
              <div className="entries-filters">
                <input
                  placeholder="Buscar por external_game_id"
                  value={searchTerm}
                  onChange={(event) => setSearchTerm(event.target.value)}
                />
                <select
                  value={statusFilter}
                  onChange={(event) => setStatusFilter(event.target.value)}
                >
                  <option value="all">Todos</option>
                  {STATUS_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {entriesLoading ? <p className="message">Cargando entradas...</p> : null}
            {entriesError ? <p className="message message--error">{entriesError}</p> : null}

            {!entriesLoading && filteredEntries.length === 0 ? (
              <p className="message">No hay entradas para el filtro seleccionado.</p>
            ) : null}

            <div className="entries-table" role="table" aria-label="Entradas de biblioteca">
              <div className="entries-row entries-row--head" role="row">
                <span>ID</span>
                <span>Game ID</span>
                <span>Status</span>
                <span>Hours</span>
                <span>Acciones</span>
              </div>

              {filteredEntries.map((entry) => {
                const draft = editDrafts[entry.id] || {
                  status: entry.status,
                  hours_played: String(entry.hours_played),
                }

                return (
                  <div className="entries-row" key={entry.id} role="row">
                    <span>{entry.id}</span>
                    <button
                      type="button"
                      className={selectedEntryId === entry.id ? 'link active' : 'link'}
                      onClick={() => {
                        setSelectedEntry(null)
                        setSelectedEntryId(entry.id)
                      }}
                    >
                      {entry.external_game_id}
                    </button>
                    <select
                      value={draft.status}
                      onChange={(event) =>
                        handleDraftChange(entry.id, 'status', event.target.value)
                      }
                    >
                      {STATUS_OPTIONS.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                    <input
                      type="number"
                      min="0"
                      step="1"
                      value={draft.hours_played}
                      onChange={(event) =>
                        handleDraftChange(entry.id, 'hours_played', event.target.value)
                      }
                    />
                    <button
                      type="button"
                      onClick={() => handleUpdateEntry(entry.id)}
                      disabled={updateLoadingId === entry.id}
                    >
                      {updateLoadingId === entry.id ? 'Guardando...' : 'Guardar'}
                    </button>
                  </div>
                )
              })}
            </div>
          </section>
        </section>

        <aside className="workspace-side">
          <section className="detail-panel">
            <h2>Detalle</h2>
            {!selectedEntryId || !selectedEntry ? (
              <p className="message">Selecciona una entrada para consultar /entries/{'{id}'}/.</p>
            ) : (
              <dl>
                <div>
                  <dt>ID</dt>
                  <dd>{selectedEntry.id}</dd>
                </div>
                <div>
                  <dt>external_game_id</dt>
                  <dd>{selectedEntry.external_game_id}</dd>
                </div>
                <div>
                  <dt>status</dt>
                  <dd>{STATUS_LABELS[selectedEntry.status] || selectedEntry.status}</dd>
                </div>
                <div>
                  <dt>hours_played</dt>
                  <dd>{selectedEntry.hours_played}</dd>
                </div>
              </dl>
            )}
          </section>

          <section className="detail-panel api-panel">
            <h2>Conexion API</h2>
            <ul>
              <li>Base URL: {apiBaseUrl}</li>
              <li>Cookies de sesion: activas</li>
              <li>CORS credentials: include</li>
            </ul>
          </section>
        </aside>
      </main>
    </div>
  )
}

export default App
