# 3D Object Cards Educational System

A kid-friendly interactive learning system that combines YOLOv10 object detection with persistent 3D educational cards featuring text-to-speech capabilities.

## Features

- **Persistent Object Cards**: Objects stay visible even after leaving camera view
- **Educational Content**: Each object includes descriptions, vocabulary, and combination examples
- **Text-to-Speech**: 🔊 Speak button reads information aloud in kid-friendly voice
- **3D Interactive Models**: Touch-enabled Three.js viewers with OrbitControls
- **Single Instance Rule**: No duplicate cards for the same object type
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Memory Efficient**: Proper cleanup prevents GPU memory leaks

## Getting Started

### Quick Start
1. Ensure all .glb model files are in `static/models/`
2. Start the Flask app: `python app.py`
3. Open browser to the HTTPS URL (accept security warning)
4. Click "Start Camera" and point at objects
5. Educational cards will appear below the camera feed

### File Structure
```
static/
├── data/
│   └── objects.json          # Educational content for objects
├── models/                   # 3D model files (.glb format)
│   ├── chair.glb
│   ├── mobile.glb
│   ├── bottle.glb
│   └── default.glb           # Fallback model
└── icons/                    # Optional icon files (.png)
    ├── chair.png
    ├── phone.png
    └── bottle.png
```

## Adding New Objects

### 1. Add 3D Model Files
Place your .glb files in `static/models/` directory:
- **Required**: Object-specific .glb file (e.g., `chair.glb`)
- **Optional**: Fallback `default.glb` for missing models

### 2. Update Educational Content
Edit `static/data/objects.json` to add new entries:

```json
{
  "object_class_name": {
    "displayName": "Display Name",
    "desc": "Kid-friendly description (2-3 sentences)",
    "vocab": ["word1", "word2", "word3"],
    "combines": ["Combines with other objects", "Multiple examples"],
    "model": "/static/models/object.glb",
    "image": "/static/icons/object.png"
  }
}
```

**Required Keys:**
- `displayName`: Name shown on the card
- `desc`: Educational description for kids
- `vocab`: Array of alternative words
- `model`: Path to .glb file

**Optional Keys:**
- `combines`: How this object combines with others
- `image`: Icon path (currently not used in UI)

### 3. Map YOLO Class Names
Update the `className` in the detection handler to match your YOLO model's class names exactly:
- YOLO outputs: `"chair"`, `"mobile phone"`, `"bottle"`
- JSON keys should match these class names exactly

## Technical Architecture

### Core Functions

#### `loadObjectInfo()`
Loads educational content from `objects.json` on app startup.

#### `handleDetections(detections, classNames)`
Main entry point replacing the old `show3DModelsFromDetections()`:
- Debounces processing (500ms) to avoid rapid creation
- Enforces single-instance rule
- Calls `createObjectCard()` for new classes

#### `createObjectCard(className)`
Creates the complete educational card with:
- 3D viewer with loading spinner
- Educational content and vocabulary
- Speak button with TTS functionality
- Remove button with fade-out animation

#### `createThreeViewerForCard(viewerEl, modelPath, className)`
Three.js viewer lifecycle:
- Loads .glb models with GLTFLoader
- Sets up lighting, shadows, and ground plane
- Adds OrbitControls with damping
- Implements auto-rotation for engagement
- Handles fallback cube for missing models

#### `disposeThreeResources(resources)`
Memory cleanup function:
- Cancels animation frames
- Disposes Three.js controls and renderer
- Traverses scene to dispose geometries/materials
- Calls `forceContextLoss()` for complete cleanup

#### `speakCardInfo(info)`
Web Speech API integration:
- Reads name, description, and vocabulary
- Kid-friendly voice settings (en-US, rate 0.95, pitch 1.0)
- Button state management during playback
- Error handling for unsupported browsers

### Data Flow
1. YOLO detection → `handleDetections()`
2. Debounce → `createObjectCard()`
3. Card creation → `createThreeViewerForCard()`
4. TTS request → `speakCardInfo()`
5. User remove → `removeCard()` → `disposeThreeResources()`

## Testing Instructions

### Desktop Testing
1. **Start the application**
   ```bash
   python app.py
   ```
   Open browser to: `https://127.0.0.1:5000`

2. **Test Object Detection**
   - Click "Start Camera" and allow camera access
   - Point camera at a chair, phone, or bottle
   - **Expected**: Object card appears below camera feed

3. **Test Persistence**
   - Let the object leave camera view
   - **Expected**: Card remains visible until manually removed

4. **Test Single Instance**
   - Show multiple chairs to camera
   - **Expected**: Only one chair card appears

5. **Test Text-to-Speech**
   - Click 🔊 Speak button on any card
   - **Expected**: Content reads aloud in clear voice

6. **Test Removal**
   - Click ❌ Remove button
   - **Expected**: Card fades out and disappears

### Mobile Testing
1. **On phone/tablet**: Navigate to your computer's IP address
   - Find IP: Run `ipconfig` on Windows or `ifconfig` on Mac/Linux
   - URL: `https://YOUR-IP:5000`

2. **Test Touch Interactions**
   - **3D Viewer**: Pinch to zoom, swipe to rotate
   - **Speak Button**: Tap to start/stop speech
   - **Remove Button**: Tap ❌ to remove card

3. **Test Responsive Layout**
   - **Tablet (≤768px)**: Cards should be 320px wide
   - **Mobile (≤480px)**: Cards should be 260px wide
   - **Desktop (≥1200px)**: Cards should be 450px wide

### Performance Testing
1. **Memory Check**
   - Open browser DevTools (F12)
   - Go to Performance tab
   - Create and remove several cards
   - **Expected**: No continuous memory growth

2. **GPU Memory Check**
   - DevTools → Performance → Memory
   - **Expected**: GPU memory freed after card removal

## Acceptance Criteria Checklist

### ✅ Basic Functionality
- [ ] Detect chair once → one object card appears
- [ ] Multiple chairs → still only one card
- [ ] Chair leaves camera → card remains until manual removal
- [ ] Speak button reads info clearly
- [ ] Remove button stops speech and removes card
- [ ] Card removal frees GPU memory

### ✅ 3D Viewer
- [ ] 3D model loads and displays correctly
- [ ] OrbitControls work (rotate, zoom, pan)
- [ ] Auto-rotation makes model engaging
- [ ] Fallback cube shows for missing models
- [ ] Loading spinner appears during model load

### ✅ Educational Content
- [ ] Object name displays clearly
- [ ] Description is kid-friendly and readable
- [ ] Vocabulary words show properly
- [ ] Combination examples (if provided) appear

### ✅ Mobile Responsiveness
- [ ] Cards fit screen on mobile devices
- [ ] Touch targets are large enough (≥44px)
- [ ] 3D viewer responds to touch gestures
- [ ] Text is readable on small screens

### ✅ Accessibility
- [ ] Speak button has ARIA labels
- [ ] Keyboard navigation works
- [ ] Focus indicators are visible
- [ ] TTS works with screen readers

## Troubleshooting

### Common Issues

**"No educational data found"**
- Check `objects.json` file exists and is valid JSON
- Verify YOLO class name matches JSON key exactly
- Ensure `objects.json` is in `static/data/` directory

**Model doesn't load**
- Check .glb file exists in `static/models/`
- Verify file path in `objects.json` matches actual file
- Check browser console for GLTFLoader errors

**TTS not working**
- Ensure browser supports Web Speech API
- Check if speech synthesis is enabled
- Test with different voices/languages

**Memory issues**
- Verify `disposeThreeResources()` is called on remove
- Check for unclosed animation loops
- Monitor GPU memory in DevTools

**Mobile layout problems**
- Clear browser cache
- Check CSS media queries are loading
- Test on different mobile browsers

## Future Enhancements

### Phase 2.2 Features
- [ ] localStorage persistence of active cards
- [ ] Undo toast notifications
- [ ] Enhanced ARIA labels and keyboard navigation
- [ ] Optional Flask API endpoint for dynamic content

### Phase 2.3 Advanced Features
- [ ] Pronunciation practice (record & compare)
- [ ] Quiz mode (hide name, ask kid to guess)
- [ ] Progress tracking and analytics
- [ ] Multi-language support

## Browser Support

**Recommended:**
- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

**Required Features:**
- WebGL support for 3D rendering
- Web Speech API for TTS
- MediaDevices API for camera access
- CSS Grid/Flexbox for responsive layout

## License

This educational system is designed for learning and classroom use. Ensure any 3D models used comply with appropriate licenses (CC0, CC-BY, etc.).