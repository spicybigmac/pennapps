'use client';

import React, { useEffect, useRef } from 'react';

type Props = {
	className?: string;
};

export default function MapboxClient(props: Props) {
	const mapEl = useRef<HTMLDivElement | null>(null);

	useEffect(() => {
		let destroyed = false;
		let map: import('mapbox-gl').Map | null = null;

		(async () => {
			const [{ default: mapboxgl }] = await Promise.all([
				import('mapbox-gl')
			]);

			const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN as string | undefined;
			if (!token) {
				console.warn('Missing NEXT_PUBLIC_MAPBOX_TOKEN');
				return;
			}
			mapboxgl.accessToken = token;

			map = new mapboxgl.Map({
				container: mapEl.current!,
				style: 'mapbox://styles/mapbox/streets-v12',
				center: [-77.04, 38.907],
				zoom: 10
			});

			map.on('load', () => {
				// Add custom tileset as a vector source
				const sourceId = 'custom-tileset';
				if (!map!.getSource(sourceId)) {
					map!.addSource(sourceId, {
						type: 'vector',
						url: 'mapbox://tcytseven.cmfryo9pv0t8b1mra7a1nejbz-4liue'
					});
				}

				// Try both a reasonable default and the user's suggested layer name
				const candidateSourceLayers = ['dummy', 'points', 'layer0'];

				candidateSourceLayers.forEach((layerName, idx) => {
					const layerId = `tileset-layer-${idx}`;
					if (map!.getLayer(layerId)) return;
					try {
						map!.addLayer({
							id: layerId,
							type: 'circle',
							source: sourceId,
							'source-layer': layerName,
							paint: {
								'circle-color': '#fc00e4',
								'circle-radius': 5,
								'circle-stroke-width': 1.5,
								'circle-stroke-color': '#ffffff'
							}
						});
						// Attach simple click popup if the layer exists
						map!.on('click', layerId, (e) => {
							const f = e.features?.[0];
							if (!f) return;
							const p = f.properties || {};
							const [lng, lat] = (f.geometry as any).coordinates;
							new mapboxgl.Popup()
								.setLngLat([lng, lat])
								.setHTML(`<div style="min-width:200px"><strong>Vessel</strong><br/>${p.title || 'Unknown'}<br/><small>${layerName}</small></div>`)
								.addTo(map!);
						});
					} catch {}
				});
			});
		})();

		return () => {
			destroyed = true;
			try { map?.remove(); } catch {}
		};
	}, []);

	return (
		<div ref={mapEl} className={props.className ?? ''} />
	);
}


