"use client";

import { useMemo, useState } from "react";
import Map, { Source, Layer, Marker, NavigationControl, FullscreenControl, Popup } from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";

export default function NetworkMap({ corridors }: { corridors?: any[] }) {
  const [viewState, setViewState] = useState({
    longitude: 65.0,
    latitude: 20.0,
    zoom: 3.5,
    pitch: 45,
    bearing: -10,
  });

  const [hoverInfo, setHoverInfo] = useState<{
    feature: any;
    longitude: number;
    latitude: number;
  } | null>(null);

  const MAPTILER_KEY = process.env.NEXT_PUBLIC_MAPTILER_KEY;
  const mapStyle = `https://api.maptiler.com/maps/darkmatter/style.json?key=${MAPTILER_KEY}`;

  const refineries = [
    { id: "jamnagar", name: "Jamnagar Refinery", lat: 22.37, lon: 69.7 },
    { id: "vizag", name: "Visakhapatnam Refinery", lat: 17.6868, lon: 83.2185 },
    { id: "paradip", name: "Paradip Refinery", lat: 20.3167, lon: 86.6167 },
  ];

  const corridorsGeoJSON = useMemo(() => {
    const defaultFeatures = [
      {
        type: "Feature",
        properties: { color: "#58d5d3", radius: 60, name: "Strait of Hormuz" }, 
        geometry: { type: "Point", coordinates: [56.25, 26.5667] }
      },
      {
        type: "Feature",
        properties: { color: "#58d5d3", radius: 40, name: "Bab-el-Mandeb" },
        geometry: { type: "Point", coordinates: [43.4167, 12.6167] }
      },
      {
        type: "Feature",
        properties: { color: "#58d5d3", radius: 50, name: "Suez Canal" },
        geometry: { type: "Point", coordinates: [32.5498, 29.9668] }
      }
    ];

    const features = corridors && corridors.length > 0 ? corridors.map((c: any) => {
      let color = "#58d5d3"; // Stable Transit (Primary)
      const score = c.disruption_score || 0;
      if (score > 0.6) {
        color = "#ffb4ab"; // Critical Shortfall (Error)
      } else if (score > 0.2) {
        color = "#d0bcff"; // Elevated Risk (Tertiary)
      }
      
      return {
        type: "Feature",
        properties: { color, radius: c.radius_km || 60, name: c.corridor_name },
        geometry: { type: "Point", coordinates: [c.center_lon, c.center_lat] }
      };
    }) : defaultFeatures;

    return {
      type: "FeatureCollection",
      features
    };
  }, [corridors]);

  const onHover = (event: any) => {
    const feature = event.features && event.features[0];
    if (feature) {
      setHoverInfo({
        feature,
        longitude: event.lngLat.lng,
        latitude: event.lngLat.lat
      });
    } else {
      setHoverInfo(null);
    }
  };

  return (
    <div style={{ height: "100%", width: "100%", position: "relative", background: "#0f1115" }}>
      {!MAPTILER_KEY ? (
        <div style={{ padding: "4rem", color: "var(--md-sys-color-error)", textAlign: "center", fontWeight: "bold" }}>
          MAPTILER KEY MISSING. Add NEXT_PUBLIC_MAPTILER_KEY to .env.local and restart server.
        </div>
      ) : (
        <>
        <style>{`
          .maplibregl-popup-content {
            background: var(--md-sys-color-surface-container-high, #2b2d31) !important;
            color: var(--md-sys-color-on-surface, #e2e2e9) !important;
            padding: 0.75rem 1rem !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5) !important;
            border: 1px solid rgba(255,255,255,0.05) !important;
          }
          .maplibregl-popup-tip {
            border-top-color: var(--md-sys-color-surface-container-high, #2b2d31) !important;
            border-bottom-color: var(--md-sys-color-surface-container-high, #2b2d31) !important;
          }
        `}</style>
        <Map
          {...viewState}
          onMove={evt => setViewState(evt.viewState)}
          mapStyle={mapStyle}
          interactive={true}
          interactiveLayerIds={['corridors-layer']}
          onMouseMove={onHover}
          onMouseLeave={() => setHoverInfo(null)}
        >
          <NavigationControl position="top-right" style={{ marginTop: '80px', marginRight: '20px' }} />
          <FullscreenControl position="top-right" style={{ marginRight: '20px' }} />

          <Source id="corridors" type="geojson" data={corridorsGeoJSON as any}>
            <Layer 
              id="corridors-layer" 
              type="circle" 
              paint={{
                "circle-color": ["get", "color"],
                "circle-radius": [
                  "interpolate",
                  ["linear"],
                  ["zoom"],
                  2, ["*", ["get", "radius"], 0.3],
                  5, ["*", ["get", "radius"], 0.8],
                  10, ["*", ["get", "radius"], 2.5]
                ],
                "circle-opacity": 0.25,
                "circle-stroke-width": 2,
                "circle-stroke-color": ["get", "color"]
              }} 
            />
          </Source>

          {refineries.map((ref) => (
            <Marker key={ref.id} longitude={ref.lon} latitude={ref.lat} anchor="center">
              <div 
                style={{
                  width: "12px",
                  height: "12px",
                  backgroundColor: "#fff",
                  borderRadius: "50%",
                  boxShadow: "0 0 8px 2px var(--md-sys-color-primary), 0 0 16px 4px var(--md-sys-color-primary), 0 0 32px 8px rgba(208, 188, 255, 0.4)",
                  border: "2px solid #fff",
                  animation: "pulse-glow 2s infinite",
                  cursor: "pointer"
                }}
                onMouseEnter={() => setHoverInfo({ feature: { properties: { name: ref.name, radius: "N/A" } }, longitude: ref.lon, latitude: ref.lat })}
                onMouseLeave={() => setHoverInfo(null)}
              />
            </Marker>
          ))}

          {hoverInfo && (
            <Popup
              longitude={hoverInfo.longitude}
              latitude={hoverInfo.latitude}
              closeButton={false}
              closeOnClick={false}
              anchor="bottom"
              style={{ zIndex: 1000 }}
            >
              <div style={{ fontFamily: 'var(--md-typescale-body-medium-font), sans-serif' }}>
                <strong style={{ display: 'block', marginBottom: '4px', fontSize: '0.875rem', fontWeight: 500, letterSpacing: '0.1px' }}>{hoverInfo.feature.properties.name}</strong>
                {hoverInfo.feature.properties.radius !== "N/A" && (
                  <span style={{ fontSize: '0.75rem', color: 'var(--md-sys-color-on-surface-variant)', letterSpacing: '0.5px' }}>Zone Radius: {hoverInfo.feature.properties.radius}km</span>
                )}
              </div>
            </Popup>
          )}
        </Map>
        </>
      )}

      {/* Floating Legend */}
      <div style={{
        position: 'absolute',
        top: '96px',
        left: '24px',
        background: 'rgba(20, 20, 20, 0.75)',
        backdropFilter: 'blur(12px)',
        padding: '1.25rem',
        borderRadius: '16px',
        border: '1px solid rgba(255, 255, 255, 0.05)',
        boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
        zIndex: 50,
        color: 'var(--md-sys-color-on-surface)',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.75rem'
      }}>
        <h4 style={{ margin: 0, fontSize: '0.875rem', fontWeight: 500, letterSpacing: '0.5px' }}>CORRIDOR STATUS</h4>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', font: 'var(--md-typescale-label-small-font)', fontSize: '0.6875rem', fontWeight: 500, letterSpacing: '0.5px', textTransform: 'uppercase' }}>
          <span style={{ width: '12px', height: '12px', background: 'var(--md-sys-color-error)', borderRadius: '50%' }} /> Critical Shortfall
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', font: 'var(--md-typescale-label-small-font)', fontSize: '0.6875rem', fontWeight: 500, letterSpacing: '0.5px', textTransform: 'uppercase' }}>
          <span style={{ width: '12px', height: '12px', background: 'var(--md-sys-color-tertiary)', borderRadius: '50%' }} /> Elevated Risk
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', font: 'var(--md-typescale-label-small-font)', fontSize: '0.6875rem', fontWeight: 500, letterSpacing: '0.5px', textTransform: 'uppercase' }}>
          <span style={{ width: '12px', height: '12px', background: 'var(--md-sys-color-primary)', borderRadius: '50%' }} /> Stable Transit
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', font: 'var(--md-typescale-label-small-font)', fontSize: '0.6875rem', fontWeight: 500, letterSpacing: '0.5px', textTransform: 'uppercase', marginTop: '0.25rem' }}>
          <span style={{ width: '12px', height: '12px', background: '#fff', borderRadius: '50%', boxShadow: "0 0 8px var(--md-sys-color-primary)" }} /> Refinery Target
        </div>
      </div>
    </div>
  );
}
