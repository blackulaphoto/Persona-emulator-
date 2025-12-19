# FRONTEND INTEGRATION GUIDE

## Setup Instructions

### 1. Install Dependencies

```bash
cd frontend

# If using npm:
npm install

# If using yarn:
yarn install

# No new dependencies needed! All components use built-in Next.js features.
```

### 2. Environment Configuration

Create or update `.env.local`:

```bash
# API URL (adjust for your backend)
NEXT_PUBLIC_API_URL=http://localhost:8000

# For production:
# NEXT_PUBLIC_API_URL=https://your-api.railway.app
```

### 3. File Structure

Place the files in your Next.js project:

```
frontend/
├── app/
│   └── templates/
│       └── page.tsx                 # Main templates page
├── components/
│   ├── templates/
│   │   ├── TemplateBrowser.tsx     # Template list/grid
│   │   └── TemplateDetailsModal.tsx # Full template details
│   └── remix/
│       └── SnapshotComparison.tsx   # Side-by-side comparison
└── lib/
    └── api/
        └── templates.ts              # API client functions
```

### 4. Navigation Integration

Add link to templates page in your existing navigation:

```tsx
// In your layout or nav component:
<Link href="/templates">
  <button className="...">
    Clinical Templates
  </button>
</Link>
```

### 5. Optional: Add to Personas Page

You can add a "Create from Template" button to your personas list:

```tsx
// In app/personas/page.tsx:
import { useRouter } from 'next/navigation';

function PersonasPage() {
  const router = useRouter();
  
  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1>My Personas</h1>
        <div className="flex gap-3">
          <button onClick={() => router.push('/personas/new')}>
            Create New Persona
          </button>
          <button 
            onClick={() => router.push('/templates')}
            className="bg-purple-600 text-white px-4 py-2 rounded-lg"
          >
            Create from Template
          </button>
        </div>
      </div>
      {/* Rest of personas list */}
    </div>
  );
}
```

---

## Component Usage

### Template Browser

```tsx
import TemplateBrowser from '@/components/templates/TemplateBrowser';

<TemplateBrowser 
  onSelectTemplate={(templateId) => {
    // Handle template selection
    setSelectedTemplate(templateId);
  }}
/>
```

### Template Details Modal

```tsx
import TemplateDetailsModal from '@/components/templates/TemplateDetailsModal';

{selectedTemplateId && (
  <TemplateDetailsModal
    templateId={selectedTemplateId}
    onClose={() => setSelectedTemplateId(null)}
    onCreatePersona={(templateId, templateName) => {
      // Handle persona creation
      console.log('Creating persona from', templateName);
    }}
  />
)}
```

### Snapshot Comparison

```tsx
import SnapshotComparisonView from '@/components/remix/SnapshotComparison';

<SnapshotComparisonView
  snapshotId1="baseline-snapshot-id"
  snapshotId2="modified-snapshot-id"
  onClose={() => setShowComparison(false)}
/>
```

---

## API Client Usage

### Templates API

```tsx
import { templatesAPI } from '@/lib/api/templates';

// List all templates
const templates = await templatesAPI.list();

// Filter by disorder type
const bpdTemplates = await templatesAPI.list('BPD');

// Get template details
const template = await templatesAPI.get('bpd_classic_pathway');

// Create persona from template
const result = await templatesAPI.createPersona(
  'bpd_classic_pathway',
  'Emma - BPD Case'
);

// Apply experiences
const applied = await templatesAPI.applyExperiences(
  personaId,
  'bpd_classic_pathway',
  [0, 1, 2] // Optional: specific experience indices
);
```

### Remix API

```tsx
import { remixAPI } from '@/lib/api/templates';

// Create snapshot
const snapshot = await remixAPI.createSnapshot(
  personaId,
  'Baseline - Untreated',
  'Before any interventions'
);

// List snapshots
const snapshots = await remixAPI.listSnapshots(personaId);

// Compare snapshots
const comparison = await remixAPI.compareSnapshots(
  snapshotId1,
  snapshotId2
);

// Get intervention impact
const impact = await remixAPI.getInterventionImpact(
  personaId,
  baselineSnapshotId
);

// Get remix suggestions
const suggestions = await remixAPI.getSuggestions(
  personaId,
  'bpd_classic_pathway'
);
```

---

## Error Handling

All API functions throw `APIError` on failure:

```tsx
import { templatesAPI, APIError } from '@/lib/api/templates';

try {
  const templates = await templatesAPI.list();
} catch (err) {
  if (err instanceof APIError) {
    if (err.status === 404) {
      console.log('Feature not enabled');
    } else {
      console.error('API error:', err.message);
    }
  }
}
```

---

## Styling

Components use **Tailwind CSS** classes. Ensure your `tailwind.config.js` includes:

```js
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      // Your custom theme
    },
  },
}
```

---

## Feature Detection

Check if clinical templates feature is enabled:

```tsx
async function checkFeature() {
  try {
    await templatesAPI.list();
    return true; // Feature enabled
  } catch (err) {
    if (err instanceof APIError && err.status === 404) {
      return false; // Feature disabled
    }
    throw err; // Other error
  }
}
```

---

## Complete User Flow Example

```tsx
'use client';

import { useState } from 'react';
import { templatesAPI, remixAPI } from '@/lib/api/templates';
import TemplateBrowser from '@/components/templates/TemplateBrowser';
import TemplateDetailsModal from '@/components/templates/TemplateDetailsModal';

export default function CompleteFlow() {
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [createdPersona, setCreatedPersona] = useState(null);

  async function handleCreatePersona(templateId, templateName) {
    // 1. Create persona
    const result = await templatesAPI.createPersona(templateId);
    setCreatedPersona(result);
    
    // 2. Apply all experiences
    await templatesAPI.applyExperiences(
      result.persona_id,
      templateId
    );
    
    // 3. Create baseline snapshot
    await remixAPI.createSnapshot(
      result.persona_id,
      'Baseline - Full Development',
      'Complete disorder development without intervention'
    );
    
    // Now persona is ready for comparison!
    alert('Persona created and baseline saved!');
  }

  return (
    <div>
      <TemplateBrowser onSelectTemplate={setSelectedTemplate} />
      
      {selectedTemplate && (
        <TemplateDetailsModal
          templateId={selectedTemplate}
          onClose={() => setSelectedTemplate(null)}
          onCreatePersona={handleCreatePersona}
        />
      )}
    </div>
  );
}
```

---

## TypeScript Support

All components and API functions are fully typed. Import types as needed:

```tsx
import type { 
  Template, 
  TemplateDetails, 
  TimelineSnapshot,
  SnapshotComparison 
} from '@/lib/api/templates';
```

---

## Testing

To test the frontend without backend:

1. Mock the API functions:

```tsx
// In tests or development
jest.mock('@/lib/api/templates', () => ({
  templatesAPI: {
    list: jest.fn().mockResolvedValue([
      {
        id: 'test-template',
        name: 'Test Template',
        disorder_type: 'BPD',
        // ...
      }
    ]),
  },
}));
```

2. Or use feature flags to conditionally show:

```tsx
const [featureEnabled, setFeatureEnabled] = useState(false);

useEffect(() => {
  templatesAPI.list()
    .then(() => setFeatureEnabled(true))
    .catch(() => setFeatureEnabled(false));
}, []);

if (!featureEnabled) {
  return <div>Clinical templates feature not available</div>;
}
```

---

## Next Steps

1. **Add to existing persona pages**: Show template info if persona was created from template
2. **Add snapshot list**: Show saved snapshots on persona detail page
3. **Add comparison UI**: Button to compare current state with snapshot
4. **Add remix suggestions**: Show template suggestions on persona page

---

## Need Help?

Common issues:

1. **CORS errors**: Ensure backend has correct CORS configuration
2. **404 on API calls**: Check NEXT_PUBLIC_API_URL and feature flags
3. **Styling issues**: Verify Tailwind CSS is configured correctly
4. **Type errors**: Ensure TypeScript is configured in tsconfig.json

All components are self-contained and don't require additional setup beyond Next.js + Tailwind!
