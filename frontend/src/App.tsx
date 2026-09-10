import { Route, Routes } from "react-router-dom";

import { AppLayout } from "./layouts/AppLayout";
import { Anomalies } from "./pages/Anomalies";
import { DeviceDetail } from "./pages/DeviceDetail";
import { Devices } from "./pages/Devices";
import { Overview } from "./pages/Overview";
import { PowerAnalytics } from "./pages/PowerAnalytics";
import { System } from "./pages/System";
import { Telemetry } from "./pages/Telemetry";
import { UsageAnalytics } from "./pages/UsageAnalytics";

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Overview />} />
        <Route path="devices" element={<Devices />} />
        <Route path="devices/:deviceId" element={<DeviceDetail />} />
        <Route path="analytics/usage" element={<UsageAnalytics />} />
        <Route path="analytics/power" element={<PowerAnalytics />} />
        <Route path="anomalies" element={<Anomalies />} />
        <Route path="telemetry" element={<Telemetry />} />
        <Route path="system" element={<System />} />
      </Route>
    </Routes>
  );
}
