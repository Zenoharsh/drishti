"use client";

import dynamic from "next/dynamic";

const NetworkMap = dynamic(() => import("./NetworkMap"), {
  ssr: false,
  loading: () => <p>Loading Digital Twin Network...</p>
});

export default function MapWrapper({ corridors, vessels, refineries }: { corridors?: any[], vessels?: any[], refineries?: any[] }) {
  return <NetworkMap corridors={corridors} vessels={vessels} refineries={refineries} />;
}

