<template>
  <Dropdown :options="agentStatusOptions" placement="right-start">
    <template #default="{ open }">
      <Button
        :label="agentStatusLabel"
        :theme="agentStatusTheme"
        variant="solid"
        :loading="isUpdatingPresence"
        class="w-full justify-start"
      >
        <template #prefix>
          <IndicatorIcon :class="agentStatusIndicatorClass" />
        </template>
        <template #suffix>
          <FeatherIcon :name="open ? 'chevron-up' : 'chevron-down'" class="h-4 w-4" />
        </template>
      </Button>
    </template>
  </Dropdown>
</template>

<script setup lang="ts">
import { IndicatorIcon } from "@/components/icons";
import { __ } from "@/translation";
import { Dropdown, FeatherIcon } from "frappe-ui";
import { computed, h, onMounted, onUnmounted, ref } from "vue";

type AgentStatus = "Online" | "Offline" | "Break" | "In Meeting";

const agentStatus = ref<AgentStatus>("Offline");
const isUpdatingPresence = ref(false);
let hasSentOfflineBeacon = false;

const statusMeta: Record<
  AgentStatus,
  { theme: string; indicatorClass: string; label: string }
> = {
  Online: { theme: "green", indicatorClass: "text-green-500", label: "Online" },
  Offline: { theme: "red", indicatorClass: "text-red-500", label: "Offline" },
  Break: { theme: "orange", indicatorClass: "text-orange-500", label: "Break" },
  "In Meeting": { theme: "blue", indicatorClass: "text-blue-500", label: "In Meeting" },
};

const agentStatusLabel = computed(() => __(statusMeta[agentStatus.value].label));
const agentStatusTheme = computed(() => statusMeta[agentStatus.value].theme);
const agentStatusIndicatorClass = computed(() => statusMeta[agentStatus.value].indicatorClass);

const agentStatusOptions = computed(() => [
  {
    label: __("Online"),
    onClick: () => setAgentStatus("Online"),
    icon: () => h(IndicatorIcon, { class: "text-green-500" }),
  },
  {
    label: __("Offline"),
    onClick: () => setAgentStatus("Offline"),
    icon: () => h(IndicatorIcon, { class: "text-red-500" }),
  },
  {
    label: __("Break"),
    onClick: () => setAgentStatus("Break"),
    icon: () => h(IndicatorIcon, { class: "text-orange-500" }),
  },
  {
    label: __("In Meeting"),
    onClick: () => setAgentStatus("In Meeting"),
    icon: () => h(IndicatorIcon, { class: "text-blue-500" }),
  },
]);

function getCookieValue(name: string) {
  const cookie = document.cookie
    .split(";")
    .map((item) => item.trim())
    .find((item) => item.startsWith(`${name}=`));

  return cookie ? decodeURIComponent(cookie.split("=").slice(1).join("=")) : "";
}

async function setAgentStatus(status: AgentStatus) {
  if (isUpdatingPresence.value) return;

  isUpdatingPresence.value = true;
  try {
    const csrfToken = window.csrf_token || getCookieValue("csrf_token");
    const response = await fetch("/api/method/toggle_agent_live", {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        "X-Frappe-CSRF-Token": csrfToken,
      },
      body: JSON.stringify({ cmd: "toggle_agent_live", status }),
    });

    if (!response.ok) {
      throw new Error(`Failed to set agent status to ${status}`);
    }

    const data = await response.json();
    agentStatus.value = data?.message?.status || status;
  } catch (error) {
    console.error(error);
  } finally {
    isUpdatingPresence.value = false;
  }
}

async function setAgentOnlineOnLogin() {
  try {
    const csrfToken = window.csrf_token || getCookieValue("csrf_token");
    const response = await fetch("/api/method/set_agent_online_on_login", {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        "X-Frappe-CSRF-Token": csrfToken,
      },
      body: JSON.stringify({ cmd: "set_agent_online_on_login" }),
    });

    if (!response.ok) {
      throw new Error("Failed to set agent online on login");
    }

    const data = await response.json();
    agentStatus.value = data?.message?.status || "Online";
  } catch (error) {
    console.error(error);
  }
}

function sendOfflineBeacon() {
  if (hasSentOfflineBeacon) return;
  hasSentOfflineBeacon = true;

  const csrfToken = window.csrf_token || getCookieValue("csrf_token");
  const payload = new URLSearchParams({
    cmd: "toggle_agent_live",
    status: "Offline",
  });

  if (csrfToken) {
    payload.append("csrf_token", csrfToken);
  }

  navigator.sendBeacon("/api/method/toggle_agent_live", payload);
}

onMounted(async () => {
  hasSentOfflineBeacon = false;
  await setAgentOnlineOnLogin();
  window.addEventListener("beforeunload", sendOfflineBeacon);
  window.addEventListener("pagehide", sendOfflineBeacon);
});

onUnmounted(() => {
  window.removeEventListener("beforeunload", sendOfflineBeacon);
  window.removeEventListener("pagehide", sendOfflineBeacon);
});
</script>
