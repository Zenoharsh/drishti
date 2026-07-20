"use client";

import dynamic from "next/dynamic";

const NetworkMap = dynamic(() => import("./NetworkMap"), {
  ssr: false,
  loading: () => <p>Loading Digital Twin Network...</p>
});

export default function MapWrapper({ corridors }: { corridors?: any[] }) {
  return <NetworkMap corridors={corridors} />;
}

