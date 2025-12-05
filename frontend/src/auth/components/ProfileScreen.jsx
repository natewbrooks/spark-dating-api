import { useAuth } from '@contexts/AuthContext'
import { useCallback, useEffect, useMemo, useState } from 'react'

const DEFAULT_PHOTO =
`data:image/svg+xml;utf8,${encodeURIComponent(`
  <svg xmlns="http://www.w3.org/2000/svg" width="600" height="800" viewBox="0 0 600 800">
    <defs>
      <linearGradient id="grad" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" style="stop-color:#2c2a2a;stop-opacity:1" />
        <stop offset="100%" style="stop-color:#171616;stop-opacity:1" />
      </linearGradient>
    </defs>
    <rect width="600" height="800" fill="url(#grad)" />
    <g fill="#555" font-family="Arial, Helvetica, sans-serif" font-size="46" text-anchor="middle">
      <text x="300" y="360">upload</text>
      <text x="300" y="420">a photo</text>
    </g>
  </svg>
`)}`

function formatValue(value) {
  if (!value) return 'add info'
  if (Array.isArray(value)) {
    return value.length ? value.join(', ') : 'add info'
  }
  const cleaned = String(value)
    .replace(/_/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
  return cleaned
    ? cleaned[0].toUpperCase() + cleaned.slice(1).toLowerCase()
    : 'add info'
}

function calculateAge(dateString) {
  if (!dateString) return null
  const birthDate = new Date(dateString)
  if (Number.isNaN(birthDate.getTime())) return null
  const today = new Date()
  let age = today.getFullYear() - birthDate.getFullYear()
  const m = today.getMonth() - birthDate.getMonth()
  if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) age -= 1
  return age
}

const StatBadge = ({ icon, label }) => (
  <div className="flex items-center gap-1 text-xs uppercase tracking-[0.35em] text-[#C7C4A7]">
    <span className="text-primary">{icon}</span>
    <span className="tracking-[0.25em]">{label}</span>
  </div>
)

const SectionCard = ({ title, children }) => (
  <div className="space-y-2 rounded-3xl bg-[#272323] p-4 shadow-[0_25px_55px_rgba(0,0,0,0.45)]">
    <p className="text-xs uppercase tracking-[0.4em] text-[#C7C4A7]">{title}</p>
    <div className="text-lg leading-relaxed text-white">{children}</div>
  </div>
)

const FloatingButton = ({ icon, onClick, label }) => (
  <button
    aria-label={label}
    onClick={onClick}
    className="absolute -right-3 -bottom-3 grid h-12 w-12 place-content-center rounded-full bg-primary text-2xl text-darkest shadow-lg hover:opacity-80"
  >
    {icon}
  </button>
)

function ProfileView({
  userInfo,
  profile,
  gender,
  orientation,
  interests,
  photoUrl,
  onEdit,
}) {
  const languages = profile?.languages_spoken ?? []
  const age = calculateAge(userInfo?.birthdate)
  return (
    <div className="mx-auto w-full max-w-md space-y-6 rounded-[48px] bg-[#1C1A1A] p-6 text-white shadow-[0_25px_55px_rgba(0,0,0,0.6)]">
      <header className="flex items-center justify-between text-lg uppercase tracking-[0.4em] text-primary">
        <span className="text-white">your profile</span>
        <span>spark</span>
      </header>

      <div className="overflow-hidden rounded-[36px]">
        <img
          src={photoUrl || DEFAULT_PHOTO}
          alt="primary profile"
          className="aspect-[10/12] w-full object-cover"
        />
      </div>

      <div className="flex flex-wrap gap-x-4 gap-y-2">
        <StatBadge icon="♀" label={formatValue(gender?.name)} />
        {age !== null && <StatBadge icon="🎂" label={`${age}`} />}
        <StatBadge icon="📍" label={formatValue(profile?.location_label || profile?.location)} />
        <StatBadge icon="👁" label={profile?.show_precise_location ? 'Yes' : 'No'} />
      </div>

      <SectionCard title="about me">
        {profile?.bio ? profile.bio : 'Share something memorable about yourself.'}
      </SectionCard>

      <div className="relative">
        <SectionCard title="relationship goal">
          {profile?.relationship_goal ? formatValue(profile.relationship_goal) : 'Let people know what you are looking for.'}
        </SectionCard>
        <FloatingButton icon="✎" label="Edit profile" onClick={onEdit} />
      </div>

      <SectionCard title="details">
        <dl className="space-y-2 text-base">
          <div className="flex justify-between">
            <dt className="text-[#C7C4A7]">Orientation</dt>
            <dd>{formatValue(orientation?.name)}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-[#C7C4A7]">Pronouns</dt>
            <dd>{formatValue(profile?.pronouns)}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-[#C7C4A7]">Languages</dt>
            {/* <dd className="text-right">{languages.length ? languages.join(', ') : 'add info'}</dd> */}
          </div>
        </dl>
      </SectionCard>

      {interests.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-[0.4em] text-[#C7C4A7]">interests</p>
          <div className="flex flex-wrap gap-2">
            {interests.map((interest) => (
              <span key={interest.id} className="rounded-full bg-[#2f2b2b] px-3 py-1 text-sm text-primary">
                {interest.name}
              </span>
            ))}
          </div>
        </div>
      )}

      <nav className="flex items-center justify-between rounded-full bg-[#0F0E0E] px-6 py-3 text-2xl text-primary">
        <button type="button" className="hover:opacity-80" aria-label="Explore">
          ⚡
        </button>
        <button type="button" className="hover:opacity-80" aria-label="Chat">
          💬
        </button>
        <button type="button" className="text-white" aria-label="Profile">
          👤
        </button>
        <button type="button" className="hover:opacity-80" aria-label="Settings">
          ⚙️
        </button>
      </nav>
    </div>
  )
}

function ProfileEdit({
  profile,
  photoUrl,
  saving,
  onCancel,
  onSubmit,
}) {
  const [formState, setFormState] = useState({
    bio: profile?.bio || '',
    location_label: profile?.location_label || '',
    location: profile?.location || '',
    pronouns: profile?.pronouns || '',
    relationship_goal: profile?.relationship_goal || '',
    languages_spoken: (profile?.languages_spoken ?? []).join(', '),
    show_precise_location: Boolean(profile?.show_precise_location),
  })

  useEffect(() => {
    setFormState({
      bio: profile?.bio || '',
      location_label: profile?.location_label || '',
      location: profile?.location || '',
      pronouns: profile?.pronouns || '',
      relationship_goal: profile?.relationship_goal || '',
      languages_spoken: (profile?.languages_spoken ?? []).join(', '),
      show_precise_location: Boolean(profile?.show_precise_location),
    })
  }, [profile])

  const updateField = (key, value) => {
    setFormState((prev) => ({ ...prev, [key]: value }))
  }

  const submit = (e) => {
    e.preventDefault()
    const languages = formState.languages_spoken
      ? formState.languages_spoken.split(',').map((lang) => lang.trim()).filter(Boolean)
      : []
    onSubmit({
      bio: formState.bio,
      location_label: formState.location_label,
      location: formState.location,
      pronouns: formState.pronouns,
      relationship_goal: formState.relationship_goal,
      languages_spoken: languages,
      show_precise_location: formState.show_precise_location,
    })
  }

  return (
    <form
      onSubmit={submit}
      className="mx-auto w-full max-w-md space-y-6 rounded-[48px] bg-[#1C1A1A] p-6 text-white shadow-[0_25px_55px_rgba(0,0,0,0.6)]"
    >
      <header className="flex items-center justify-between text-lg uppercase tracking-[0.4em] text-primary">
        <span className="text-white">edit profile</span>
        <span>spark</span>
      </header>

      <div className="overflow-hidden rounded-[36px]">
        <img
          src={photoUrl || DEFAULT_PHOTO}
          alt="primary profile"
          className="aspect-[10/12] w-full object-cover"
        />
      </div>

      <div className="flex flex-col space-y-4">
        <label className="space-y-2 text-sm uppercase tracking-[0.3em] text-[#C7C4A7]">
          location label
          <input
            type="text"
            className="w-full rounded-2xl bg-[#272323] px-4 py-3 text-lg text-white outline-none focus:ring-2 focus:ring-primary"
            value={formState.location_label}
            onChange={(e) => updateField('location_label', e.target.value)}
          />
        </label>

        <label className="space-y-2 text-sm uppercase tracking-[0.3em] text-[#C7C4A7]">
          actual location
          <input
            type="text"
            className="w-full rounded-2xl bg-[#272323] px-4 py-3 text-lg text-white outline-none focus:ring-2 focus:ring-primary"
            value={formState.location}
            onChange={(e) => updateField('location', e.target.value)}
          />
        </label>

        <label className="space-y-2 text-sm uppercase tracking-[0.3em] text-[#C7C4A7]">
          pronouns
          <input
            type="text"
            className="w-full rounded-2xl bg-[#272323] px-4 py-3 text-lg text-white outline-none focus:ring-2 focus:ring-primary"
            value={formState.pronouns}
            onChange={(e) => updateField('pronouns', e.target.value)}
          />
        </label>

        <label className="space-y-2 text-sm uppercase tracking-[0.3em] text-[#C7C4A7]">
          languages spoken
          <input
            type="text"
            className="w-full rounded-2xl bg-[#272323] px-4 py-3 text-lg text-white outline-none focus:ring-2 focus:ring-primary"
            value={formState.languages_spoken}
            onChange={(e) => updateField('languages_spoken', e.target.value)}
            placeholder="english, spanish"
          />
        </label>

        <label className="space-y-2 text-sm uppercase tracking-[0.3em] text-[#C7C4A7]">
          relationship goal
          <input
            type="text"
            className="w-full rounded-2xl bg-[#272323] px-4 py-3 text-lg text-white outline-none focus:ring-2 focus:ring-primary"
            value={formState.relationship_goal}
            onChange={(e) => updateField('relationship_goal', e.target.value)}
          />
        </label>

        <label className="space-y-2 text-sm uppercase tracking-[0.3em] text-[#C7C4A7]">
          about me
          <textarea
            className="w-full rounded-2xl bg-[#272323] px-4 py-3 text-lg text-white outline-none focus:ring-2 focus:ring-primary"
            rows={4}
            value={formState.bio}
            onChange={(e) => updateField('bio', e.target.value)}
            placeholder="Share a quick story or fun fact"
          />
        </label>

        <label className="flex items-center justify-between rounded-2xl bg-[#272323] px-4 py-3 text-sm uppercase tracking-[0.3em] text-[#C7C4A7]">
          show precise location
          <input
            type="checkbox"
            className="h-5 w-5 accent-primary"
            checked={formState.show_precise_location}
            onChange={(e) => updateField('show_precise_location', e.target.checked)}
          />
        </label>
      </div>

      <div className="flex items-center justify-between">
        <button
          type="button"
          className="rounded-full bg-[#2f2b2b] px-6 py-3 uppercase tracking-[0.3em] text-white hover:opacity-80"
          onClick={onCancel}
          disabled={saving}
        >
          cancel
        </button>
        <button
          type="submit"
          className="grid h-12 w-12 place-content-center rounded-full bg-primary text-2xl text-darkest shadow-lg hover:opacity-80 disabled:opacity-50"
          disabled={saving}
          aria-label="Save profile"
        >
          ✓
        </button>
      </div>
    </form>
  )
}

export default function ProfileScreen() {
  const { fetchWithAuth, isAuthenticated } = useAuth()
  const [userInfo, setUserInfo] = useState(null)
  const [profile, setProfile] = useState(null)
  const [gender, setGender] = useState(null)
  const [orientation, setOrientation] = useState(null)
  const [interests, setInterests] = useState([])
  const [photos, setPhotos] = useState([])
  const [mode, setMode] = useState('view')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const loadData = useCallback(async () => {
    if (!isAuthenticated) return
    setLoading(true)
    setError('')
    try {
      const [
        profileRes,
        userRes,
        genderRes,
        orientationRes,
        interestsRes,
        photosRes,
      ] = await Promise.all([
        fetchWithAuth('/profile/me'),
        fetchWithAuth('/user/me'),
        fetchWithAuth('/profile/me/gender'),
        fetchWithAuth('/profile/me/orientation'),
        fetchWithAuth('/profile/me/interests'),
        fetchWithAuth('/profile/me/photos'),
      ])

      if (profileRes.ok) {
        setProfile(await profileRes.json())
      } else if (profileRes.status === 404) {
        setProfile(null)
      } else {
        throw new Error('Failed to load profile')
      }

      if (userRes.ok) setUserInfo(await userRes.json())
      if (genderRes.ok) setGender(await genderRes.json())
      if (orientationRes.ok) setOrientation(await orientationRes.json())
      if (interestsRes.ok) setInterests(await interestsRes.json())
      if (photosRes.ok) setPhotos(await photosRes.json())
    } catch (err) {
      console.error(err)
      setError(err?.message || 'Something went wrong while loading your profile.')
    } finally {
      setLoading(false)
    }
  }, [fetchWithAuth, isAuthenticated])

  useEffect(() => {
    loadData()
  }, [loadData])

  const primaryPhoto = useMemo(() => {
    if (!photos?.length) return null
    const preferred = photos.find((photo) => photo?.metadata?.is_primary)
    return (preferred || photos[0])?.url || null
  }, [photos])

  const interestNames = useMemo(
    () => interests.map((item) => item.name),
    [interests],
  )

  const handleSave = useCallback(
    async (partialData) => {
      if (!profile) return
      setSaving(true)
      setError('')
      try {
        const payload = {
          bio: partialData.bio ?? profile.bio ?? '',
          drug_use: profile.drug_use ?? false,
          weed_use: profile.weed_use ?? false,
          gender: gender?.name,
          orientation: orientation?.name,
          interests: interestNames,
          location: partialData.location ?? profile.location ?? '',
          location_label: partialData.location_label ?? profile.location_label ?? '',
          show_precise_location:
            typeof partialData.show_precise_location === 'boolean'
              ? partialData.show_precise_location
              : Boolean(profile.show_precise_location),
          pronouns: partialData.pronouns ?? profile.pronouns,
          languages_spoken: partialData.languages_spoken ?? profile.languages_spoken ?? [],
          school: profile.school,
          occupation: profile.occupation,
          relationship_goal: partialData.relationship_goal ?? profile.relationship_goal,
          personality_type: profile.personality_type,
          love_language: profile.love_language,
          attachment_style: profile.attachment_style,
          political_view: profile.political_view,
          zodiac_sign: profile.zodiac_sign,
          religion: profile.religion,
          diet: profile.diet,
          exercise_frequency: profile.exercise_frequency,
          pets: profile.pets,
          smoke_frequency: profile.smoke_frequency,
          drink_frequency: profile.drink_frequency,
          sleep_schedule: profile.sleep_schedule,
        }

        if (!payload.gender || !payload.orientation) {
          throw new Error('Gender and orientation must be set before updating your profile.')
        }

        const res = await fetchWithAuth('/profile/me', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })

        if (!res.ok) {
          const errBody = await res.json().catch(() => ({}))
          throw new Error(errBody?.detail || errBody?.message || 'Unable to save profile')
        }
        await loadData()
        setMode('view')
      } catch (err) {
        console.error(err)
        setError(err?.message || 'Failed to save profile changes.')
      } finally {
        setSaving(false)
      }
    },
    [fetchWithAuth, gender?.name, interestNames, loadData, orientation?.name, profile],
  )

  if (!isAuthenticated) {
    return null
  }

  if (loading) {
    return (
      <div className="text-center text-white">
        <p>Loading your profile...</p>
      </div>
    )
  }

  if (!profile) {
    return (
      <div className="w-full max-w-md rounded-3xl bg-[#1C1A1A] p-8 text-center text-white shadow-[0_25px_55px_rgba(0,0,0,0.6)]">
        <p className="text-2xl font-title uppercase tracking-[0.35em]">no profile yet</p>
        <p className="mt-4 text-lg">
          Tell people about yourself to unlock the live chat experience.
        </p>
      </div>
    )
  }

  return (
    <div className="w-full">
      {error && (
        <div className="mb-4 rounded-xl bg-red-500/15 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}
      {mode === 'view' ? (
        <ProfileView
          userInfo={userInfo}
          profile={profile}
          gender={gender}
          orientation={orientation}
          interests={interests}
          photoUrl={primaryPhoto}
          onEdit={() => setMode('edit')}
        />
      ) : (
        <ProfileEdit
          profile={profile}
          photoUrl={primaryPhoto}
          saving={saving}
          onCancel={() => setMode('view')}
          onSubmit={handleSave}
        />
      )}
    </div>
  )
}
