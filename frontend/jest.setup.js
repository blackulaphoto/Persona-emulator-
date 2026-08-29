import '@testing-library/jest-dom'

// React 18 + jest-environment-jsdom doesn't self-detect as an act()
// environment, which spams "not configured to support act(...)" warnings on
// any test that triggers a state update from an async callback (e.g. via
// @testing-library/user-event) even when properly wrapped in act(). This is
// the documented fix.
global.IS_REACT_ACT_ENVIRONMENT = true
