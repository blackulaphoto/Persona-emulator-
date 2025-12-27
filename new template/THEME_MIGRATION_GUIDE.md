# PROFESSIONAL THEME - COMPONENT STYLING GUIDE

## 🎨 How to Apply the New Theme

This guide shows how to update your existing components to use the new professional theme **without changing their structure**.

---

## 1️⃣ UPDATE LAYOUT (Header & Main Container)

### **frontend/app/layout.tsx**

```tsx
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-bg-tertiary min-h-screen">
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
```

---

## 2️⃣ UPDATE HEADER COMPONENT

### **frontend/components/Header.tsx**

**Replace color classes**:

```tsx
export function Header() {
  return (
    <header className="header sticky top-0 z-50">
      <div className="container-snap py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 hover:opacity-90 transition-opacity">
            <Image src="/logo.png" alt="Persona Evolution" width={40} height={40} />
            <div>
              <h1 className="text-xl font-serif font-bold text-text-inverse">
                Persona Evolution
              </h1>
              <p className="text-xs text-primary-300">
                Explore psychological transformation
              </p>
            </div>
          </Link>
          
          {/* Navigation */}
          <nav className="flex items-center gap-4">
            {user ? (
              <>
                <Link href="/personas" className="tab tab-inactive">
                  Dashboard
                </Link>
                <Link href="/timeline" className="tab tab-inactive">
                  Timeline
                </Link>
                <button onClick={handleLogout} className="btn btn-secondary">
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link href="/login" className="tab tab-inactive">
                  Login
                </Link>
                <Link href="/signup" className="btn btn-primary">
                  Sign Up
                </Link>
              </>
            )}
          </nav>
        </div>
      </div>
    </header>
  );
}
```

---

## 3️⃣ UPDATE PERSONA LIST PAGE

### **frontend/app/personas/page.tsx**

**Find your current persona list and update classes**:

```tsx
export default function PersonasPage() {
  return (
    <div className="container-snap py-8">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="font-serif text-4xl font-bold text-text-primary mb-2">
          Your Personas
        </h1>
        <p className="text-text-secondary">
          Explore psychological transformation through experiences and therapy
        </p>
      </div>
      
      {/* Create New Button */}
      <div className="mb-6">
        <button className="btn btn-primary">
          + Create New Persona
        </button>
      </div>
      
      {/* Personas Grid/List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {personas.map((persona) => (
          <div key={persona.id} className="card-hover cursor-pointer">
            <h3 className="font-serif text-xl font-semibold mb-2">
              {persona.name}
            </h3>
            <div className="flex items-center gap-2 mb-3">
              <span className="badge badge-primary">
                Age {persona.age}
              </span>
              <span className="badge badge-success">
                {persona.experiences_count} experiences
              </span>
            </div>
            <p className="text-sm text-text-secondary line-clamp-3">
              {persona.description}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## 4️⃣ UPDATE PERSONA DETAIL PAGE (Timeline)

### **frontend/app/personas/[id]/page.tsx**

```tsx
export default function PersonaDetailPage() {
  return (
    <div className="min-h-screen bg-bg-tertiary">
      {/* Header Section */}
      <div className="bg-bg-primary text-text-inverse">
        <div className="container-snap py-8">
          <div className="flex items-center gap-6">
            <div className="w-20 h-20 bg-primary-600 rounded-full flex items-center justify-center">
              <span className="text-3xl font-serif">
                {persona.name[0]}
              </span>
            </div>
            <div>
              <h1 className="font-serif text-3xl font-bold mb-1">
                {persona.name}
              </h1>
              <div className="flex items-center gap-3 text-sm text-primary-300">
                <span>Age {persona.age}</span>
                <span>•</span>
                <span>{persona.gender}</span>
                <span>•</span>
                <span>{persona.experiences_count} experiences</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Tabs */}
      <div className="bg-bg-card border-b border-border">
        <div className="container-snap">
          <div className="flex gap-1">
            <button className="tab tab-active">Timeline</button>
            <button className="tab tab-inactive">Experiences</button>
            <button className="tab tab-inactive">Chat</button>
            <button className="tab tab-inactive">Reports</button>
          </div>
        </div>
      </div>
      
      {/* Main Content */}
      <div className="container-snap py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Timeline */}
          <div className="lg:col-span-2">
            <div className="card">
              <h2 className="font-serif text-2xl font-semibold mb-6">
                Life Timeline
              </h2>
              {/* Timeline content */}
            </div>
          </div>
          
          {/* Sidebar */}
          <div className="sidebar">
            <div className="sidebar-header">
              Quick Reference
            </div>
            <div className="sidebar-item sidebar-item-active">
              DSM Reference
            </div>
            <div className="sidebar-item">
              Export Reports
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

## 5️⃣ UPDATE FORMS (Login/Signup)

### **frontend/app/login/page.tsx**

```tsx
export default function LoginPage() {
  return (
    <div className="min-h-screen bg-bg-tertiary flex items-center justify-center px-6">
      <div className="card max-w-md w-full">
        <h1 className="font-serif text-3xl font-bold text-center mb-6">
          Welcome Back
        </h1>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label">Email Address</label>
            <input
              type="email"
              className="input"
              placeholder="you@example.com"
            />
          </div>
          
          <div>
            <label className="label">Password</label>
            <input
              type="password"
              className="input"
              placeholder="••••••••"
            />
          </div>
          
          <button type="submit" className="btn btn-primary w-full">
            Log In
          </button>
        </form>
        
        <div className="mt-6 text-center">
          <p className="text-sm text-text-secondary">
            Don't have an account?{' '}
            <Link href="/signup" className="text-accent-600 font-medium">
              Sign up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
```

---

## 6️⃣ UPDATE TABLES (Experience List)

```tsx
<table className="table">
  <thead>
    <tr>
      <th>Date</th>
      <th>Type</th>
      <th>Description</th>
      <th>Impact</th>
    </tr>
  </thead>
  <tbody>
    {experiences.map((exp) => (
      <tr key={exp.id}>
        <td className="font-mono text-xs">{exp.date}</td>
        <td>
          <span className="badge badge-primary">{exp.category}</span>
        </td>
        <td className="font-medium">{exp.description}</td>
        <td>
          <span className="badge badge-warning">{exp.severity}</span>
        </td>
      </tr>
    ))}
  </tbody>
</table>
```

---

## 7️⃣ QUICK REFERENCE - CLASS MAPPINGS

### **Replace Old Colors with New**:

```
OLD (Organic)              →  NEW (Professional)
────────────────────────────────────────────────
bg-[#1a1d20]              →  bg-bg-primary
bg-[#2D3136]              →  bg-bg-secondary
bg-[#F8F6F1]              →  bg-bg-card
text-[#F8F6F1]            →  text-text-inverse
text-[#8B9D83]            →  text-text-secondary
text-[#5B6B4D]            →  text-accent-600
border-[#8B9D83]/20       →  border-border-light
font-['Crimson_Pro']      →  font-serif
font-['Outfit']           →  font-sans
```

---

## 8️⃣ LOADING & EMPTY STATES

```tsx
// Loading skeleton
<div className="card">
  <div className="skeleton h-8 w-3/4 mb-4" />
  <div className="skeleton h-4 w-full mb-2" />
  <div className="skeleton h-4 w-5/6" />
</div>

// Empty state
<div className="card text-center py-12">
  <p className="text-text-tertiary text-lg mb-4">
    No personas yet
  </p>
  <button className="btn btn-primary">
    Create Your First Persona
  </button>
</div>
```

---

## 🎯 MIGRATION STRATEGY

1. **Replace** `tailwind.config.js` with new version
2. **Replace** `globals.css` with new version
3. **Update components one by one**:
   - Start with layout.tsx
   - Then header
   - Then main pages (personas, detail, forms)
4. **Test locally** after each component
5. **Push when all working**

---

## ⏱️ ESTIMATED TIME

- Layout & Header: 15 min
- Persona List: 15 min
- Persona Detail: 30 min
- Forms: 15 min
- Polish & Test: 30 min

**Total: ~2 hours**

---

This keeps all your React logic intact while giving a professional clinical appearance!
