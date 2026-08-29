# Pre-design Life Builder contract

This cleanup pass does not implement the Life Builder UI. The first UX implementation must preserve unsubmitted draft experiences across accidental refreshes and navigation before **Analyze Life** runs. Client-side persistence such as `localStorage` or IndexedDB is acceptable for the first version; no server-side draft subsystem is required by this contract.

## Analyze Life and Impact Reveal

Impact Reveal is a core flow and must not depend on the Remix feature flag:

1. The frontend captures the current `PersonaResponse` before analysis.
2. The frontend submits the ordered batch of experiences.
3. The frontend fetches the post-analysis `PersonaResponse`.
4. The frontend computes and displays the difference between those two canonical responses.

When Remix is enabled, the client may additionally persist a `TimelineSnapshot` as a durable comparison point. Snapshot creation is optional and must never block or gate Analyze Life.

Draft entries must retain both `age_at_event` and `sequence_index`, because same-age ordering changes the psychological processing sequence.
