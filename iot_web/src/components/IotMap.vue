<template>
  <div
    ref="mapEl"
    class="iot-map"
    :class="`iot-map--${mapTheme}`"
    :style="{ height }"
  ></div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import 'leaflet/dist/leaflet.css'

const props = defineProps({
  points: { type: Array, default: () => [] },
  markers: { type: Array, default: () => [] },
  height: { type: String, default: '360px' },
  showTrack: { type: Boolean, default: true },
  /** @deprecated 请使用 theme="dark" */
  dark: { type: Boolean, default: false },
  /** default | dark | dashboard */
  theme: { type: String, default: '' },
})

const mapTheme = computed(() => {
  if (props.theme) return props.theme
  return props.dark ? 'dark' : 'default'
})

const TILE_LAYERS = {
  default: {
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '&copy; OpenStreetMap',
  },
  dark: {
    url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    attribution: '&copy; OpenStreetMap &copy; CARTO',
  },
  dashboard: {
    url: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
    attribution: '&copy; OpenStreetMap &copy; CARTO',
  },
}

const mapEl = ref(null)
let map = null
let layerGroup = null
let L = null

const defaultCenter = [39.9042, 116.4074]

const toLatLng = (p) => {
  const lat = p.latitude ?? p.lat
  const lng = p.longitude ?? p.lng ?? p.lon
  if (lat == null || lng == null) return null
  return [Number(lat), Number(lng)]
}

const markerColor = (item) => {
  if (item.status === 'online') return '#22c55e'
  if (item.status === 'offline') return '#64748b'
  if (item.error) return '#f59e0b'
  return '#3b82f6'
}

const containerReady = () => {
  const el = mapEl.value
  return !!(el && el.clientWidth > 0 && el.clientHeight > 0)
}

const invalidateSize = () => {
  if (!map || !containerReady()) return
  map.invalidateSize()
  render()
}

const render = () => {
  if (!map || !L || !layerGroup) return
  layerGroup.clearLayers()

  const latlngs = []
  props.points.forEach((p) => {
    const ll = toLatLng(p)
    if (!ll) return
    latlngs.push(ll)
    layerGroup.addLayer(
      L.circleMarker(ll, {
        radius: p.current ? 7 : 4,
        color: p.current ? '#409eff' : '#67c23a',
        fillOpacity: 0.85,
      }).bindPopup(`${p.timestamp ? new Date(p.timestamp).toLocaleString('zh-CN') : ''}<br/>${ll[0]}, ${ll[1]}`)
    )
  })

  props.markers.forEach((m) => {
    const ll = toLatLng(m)
    if (!ll) return
    const color = markerColor(m)
    const usePin = mapTheme.value === 'default' && !m.status
    if (usePin) {
      layerGroup.addLayer(
        L.marker(ll).bindPopup(m.label || m.device_name || m.device_id || '')
      )
    } else {
      layerGroup.addLayer(
        L.circleMarker(ll, {
          radius: 9,
          color: '#fff',
          weight: 2,
          fillColor: color,
          fillOpacity: 0.92,
        }).bindPopup(m.label || m.device_name || m.device_id || '')
      )
    }
    latlngs.push(ll)
  })

  if (props.showTrack && latlngs.length > 1) {
    layerGroup.addLayer(L.polyline(latlngs, { color: '#409eff', weight: 3, opacity: 0.7 }))
  }

  if (latlngs.length) {
    map.fitBounds(L.latLngBounds(latlngs), { padding: [30, 30], maxZoom: mapTheme.value === 'dashboard' ? 12 : 16 })
  } else {
    map.setView(defaultCenter, mapTheme.value === 'dashboard' ? 4 : 5)
  }
}

let resizeObserver = null
let resizeRaf = 0

const bindResize = () => {
  if (typeof ResizeObserver === 'undefined' || !mapEl.value) return
  resizeObserver = new ResizeObserver(() => {
    if (resizeRaf) cancelAnimationFrame(resizeRaf)
    resizeRaf = requestAnimationFrame(() => {
      resizeRaf = 0
      invalidateSize()
    })
  })
  resizeObserver.observe(mapEl.value)
}

onMounted(async () => {
  L = (await import('leaflet')).default
  delete L.Icon.Default.prototype._getIconUrl
  L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
    iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  })
  map = L.map(mapEl.value, { zoomControl: true })
  const tile = TILE_LAYERS[mapTheme.value] || TILE_LAYERS.default
  L.tileLayer(tile.url, {
    attribution: tile.attribution,
    maxZoom: 19,
  }).addTo(map)
  layerGroup = L.layerGroup().addTo(map)
  render()
  bindResize()
  requestAnimationFrame(invalidateSize)
})

watch(() => [props.points, props.markers], () => {
  invalidateSize()
}, { deep: true })

onUnmounted(() => {
  if (resizeRaf) cancelAnimationFrame(resizeRaf)
  resizeObserver?.disconnect()
  resizeObserver = null
  if (map) {
    map.remove()
    map = null
  }
})

defineExpose({ invalidateSize })
</script>

<style scoped>
.iot-map {
  width: 100%;
  min-height: 240px;
  border-radius: 8px;
  overflow: hidden;
  z-index: 0;
  background: #e8eef4;
}

.iot-map--dashboard {
  border: 1px solid #334155;
  box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.12);
  background: #1e293b;
}

.iot-map--dashboard :deep(.leaflet-control-zoom) {
  border: none;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.35);
}

.iot-map--dashboard :deep(.leaflet-control-zoom a) {
  background: rgba(15, 23, 42, 0.88);
  color: #e2e8f0;
  border-color: #334155;
}

.iot-map--dashboard :deep(.leaflet-control-zoom a:hover) {
  background: #1e293b;
  color: #93c5fd;
}

.iot-map--dashboard :deep(.leaflet-control-attribution) {
  background: rgba(15, 23, 42, 0.75);
  color: #94a3b8;
  font-size: 10px;
}

.iot-map--dark {
  border: 1px solid #1e293b;
}
</style>
