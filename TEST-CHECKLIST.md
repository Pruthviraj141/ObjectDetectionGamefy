# 3D Object Cards - Test Checklist

Quick verification steps for all acceptance criteria. Check off each item as you test.

## Setup Verification ✅

- [ ] Flask app starts without errors
- [ ] Browser loads HTTPS page (accept security warning)
- [ ] Camera permission granted successfully
- [ ] 3D Object Cards section visible below camera
- [ ] No console errors in browser DevTools

## Core Functionality Tests ✅

### 1. Object Detection & Card Creation
- [ ] Point camera at a **chair** → Chair card appears
- [ ] Point camera at a **mobile phone** → Phone card appears  
- [ ] Point camera at a **bottle** → Bottle card appears
- [ ] Card appears below camera feed within 2 seconds

### 2. Single Instance Rule
- [ ] Show multiple chairs → Only **one** chair card appears
- [ ] Show multiple phones → Only **one** phone card appears
- [ ] New object types create new cards as expected

### 3. Persistence Testing
- [ ] Let chair leave camera view → Chair card **remains visible**
- [ ] Let phone leave camera view → Phone card **remains visible**
- [ ] Camera sees new object → New card appears alongside existing ones
- [ ] Refresh page → Cards reset (expected behavior)

### 4. Removal Functionality
- [ ] Click ❌ on chair card → Card fades out and disappears
- [ ] Click ❌ while speaking → Speech stops and card removes
- [ ] Remove one card → Other cards remain unchanged
- [ ] Removed card doesn't reappear until re-detected

## 3D Viewer Tests ✅

### 5. Model Loading
- [ ] 3D model displays in each card's viewer
- [ ] Loading spinner (⏳) appears during model load
- [ ] Model loads completely within 5 seconds
- [ ] Model is clearly visible and properly sized

### 6. Interactive Controls
- [ ] Mouse drag rotates 3D model smoothly
- [ ] Mouse wheel zooms in/out
- [ ] Model auto-rotates slowly for engagement
- [ ] Controls feel responsive (no lag)

### 6.1 3D Model Sizing
- [ ] All 3D models are clearly visible and properly sized
- [ ] Small models automatically scaled up to be visible
- [ ] Large models automatically scaled down to fit viewer
- [ ] Models maintain proper proportions
- [ ] Models positioned correctly in viewer center

### 7. Fallback Handling
- [ ] Missing .glb file shows placeholder cube
- [ ] Cube rotates to show it's interactive
- [ ] "Model not available" message appears
- [ ] No console errors for missing models

## Text-to-Speech Tests ✅

### 8. Speak Button Functionality
- [ ] Click 🔊 Speak on chair card → Speech starts
- [ ] Button changes to "🔊 Speaking..." during playback
- [ ] Content reads clearly in English accent
- [ ] Button reverts to "🔊 Speak" when finished

### 9. TTS Content Quality
- [ ] Reads object name clearly
- [ ] Reads description in full sentences
- [ ] Reads vocabulary words: "seat, stool, armchair"
- [ ] Speech pace is appropriate for children

### 10. TTS Controls
- [ ] Click speak button again during playback → Stops speech
- [ ] Click remove while speaking → Stops speech and removes
- [ ] Browser supports speech synthesis (check console)

### 10.1 Enhanced Voice Selection
- [ ] **NEW**: Dropdown menu appears with voice options
- [ ] **NEW**: "🔊 Read All Info" reads complete description
- [ ] **NEW**: "🏷️ Name Only" speaks just the object name
- [ ] **NEW**: "📚 Vocabulary" speaks only vocabulary words
- [ ] **NEW**: Voice settings button (🎵) appears in bottom-right
- [ ] **NEW**: Multiple voice options available (Google, Microsoft, etc.)
- [ ] **NEW**: Kid-friendly voice settings (slower pace, higher pitch)
- [ ] **NEW**: Smooth dropdown animations
- [ ] **NEW**: Mobile-optimized voice controls

## Educational Content Tests ✅

### 11. Content Display
- [ ] Object name shows in large, clear text
- [ ] Description is readable (not cut off)
- [ ] Vocabulary section labeled "More words:"
- [ ] All text uses kid-friendly language

### 12. Content Accuracy
- [ ] Chair card shows: "A chair is used for sitting..."
- [ ] Phone card shows: "A mobile phone helps us call..."
- [ ] Vocabulary matches expected words
- [ ] Combine examples appear (if available)

## Mobile Responsiveness Tests ✅

### 13. Mobile Layout (≤480px)
- [ ] Cards fit screen width without horizontal scroll
- [ ] Card width ≈ 260px on mobile
- [ ] Text remains readable on small screens
- [ ] Buttons are easy to tap (≥44px touch target)
- [ ] **NEW**: Scroll works when multiple objects detected
- [ ] **NEW**: Can scroll through all cards vertically on mobile
- [ ] **NEW**: Scrollbar appears and is visible
- [ ] **NEW**: Smooth scrolling behavior

### 13.1 Multiple Objects on Mobile
- [ ] Detect 3+ objects → Can scroll to see all cards
- [ ] Scroll behavior is smooth and responsive
- [ ] No layout breaking with many cards
- [ ] Touch scrolling works naturally
- [ ] All cards remain accessible via scrolling

### 14. Tablet Layout (≤768px)
- [ ] Cards width ≈ 320px on tablet
- [ ] Grid layout adjusts properly
- [ ] 3D viewer responsive and clear
- [ ] All interactions work with touch

### 15. Desktop Layout (≥1200px)
- [ ] Cards width ≈ 450px on desktop
- [ ] Grid centers content properly
- [ ] Hover effects work on mouse devices
- [ ] Layout scales appropriately

## Performance Tests ✅

### 16. Memory Management
- [ ] Create 5+ cards → No significant memory increase
- [ ] Remove all cards → Memory returns to baseline
- [ ] GPU memory freed after removal (check DevTools)
- [ ] No animation loops running after removal

### 17. Rendering Performance
- [ ] 3D models render smoothly at 60fps
- [ ] No frame drops during interactions
- [ ] Multiple cards don't impact performance
- [ ] Camera detection remains responsive

## Accessibility Tests ✅

### 18. Keyboard Navigation
- [ ] Tab key navigates to all interactive elements
- [ ] Enter/Space activates buttons
- [ ] Focus indicators visible on all buttons
- [ ] Escape key doesn't interfere (optional)

### 19. Screen Reader Support
- [ ] Speak button has descriptive ARIA label
- [ ] Remove button clearly labeled
- [ ] Card changes announced (aria-live)
- [ ] TTS readable by screen readers

## Cross-Browser Testing ✅

### 20. Browser Compatibility
- [ ] **Chrome**: All features work
- [ ] **Firefox**: All features work  
- [ ] **Safari**: All features work (if available)
- [ ] **Edge**: All features work (if available)

## Error Handling Tests ✅

### 21. Network Issues
- [ ] Disconnect internet → Objects still detected locally
- [ ] Reconnect internet → No errors or crashes
- [ ] JSON load fails → Graceful fallback (no cards)

### 22. Camera Issues
- [ ] Camera denied → Clear error message
- [ ] Camera in use → Appropriate error shown
- [ ] Camera disconnected mid-session → Handles gracefully

## User Experience Tests ✅

### 23. Kid-Friendly Design
- [ ] Colors are soft and appealing
- [ ] Text is large enough for children to read
- [ ] Buttons are clearly labeled with emojis
- [ ] Loading states are engaging (spinner with emoji)

### 24. Interaction Feedback
- [ ] Hover effects provide clear visual feedback
- [ ] Button presses have visual confirmation
- [ ] Smooth animations for all transitions
- [ ] No jarring or confusing interactions

## Final Verification ✅

### 25. Complete User Journey
1. [ ] Start camera → See video feed
2. [ ] Detect chair → Card appears below
3. [ ] Click speak → Hear description
4. [ ] Rotate 3D model → Smooth interaction  
5. [ ] Let chair leave → Card persists
6. [ ] Click remove → Card fades out
7. [ ] Detect phone → New card appears
8. [ ] Test on mobile → Responsive layout works

### 26. Production Readiness
- [ ] All console errors resolved
- [ ] Memory leaks prevented
- [ ] Mobile experience polished
- [ ] Educational content appropriate
- [ ] Performance optimized

---

## Quick Test Commands

### Desktop Test
```bash
# Start app
python app.py

# Navigate to: https://127.0.0.1:5000
# Test all checklist items above
```

### Mobile Test
```bash
# Find IP address
ipconfig  # Windows
ifconfig  # Mac/Linux

# Navigate to: https://YOUR-IP:5000
# Test responsive behavior
```

### Performance Test
```bash
# Open DevTools (F12)
# Performance tab → Record while creating/removing cards
# Memory tab → Check for leaks
```

---

## Reporting Issues

If any test fails, note:
- ✅ **PASS**: Test completed successfully
- ❌ **FAIL**: Test failed - provide error details
- ⚠️ **PARTIAL**: Test partially works - describe issue
- ❓ **SKIP**: Test couldn't be completed

**Example Report:**
- ❌ FAIL: Mobile responsive (cards too wide on iPhone)
- ⚠️ PARTIAL: TTS works but slow on Firefox
- ✅ PASS: All desktop functionality works perfectly