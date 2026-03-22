<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg font-medium text-gray-900">
          {{ __('Agent Performance') }}
        </div>
      </template>
    </LayoutHeader>

    <div class="p-5 w-full overflow-y-auto">
      <div class="mb-4 flex items-center gap-2 flex-wrap">
        <button
          v-for="item in periodOptions"
          :key="item.value"
          class="h-7 rounded border px-3 text-sm transition-colors"
          :class="
            selectedPeriod === item.value
              ? 'border-blue-500 bg-blue-50 text-blue-700'
              : 'border-gray-300 bg-white text-gray-700 hover:border-gray-400'
          "
          @click="setPeriod(item.value)"
        >
          {{ item.label }}
        </button>

        <select
          v-model="selectedTeam"
          class="h-7 rounded border border-gray-300 bg-white px-2 text-sm text-gray-700"
          @change="fetchData"
        >
          <option value="">{{ __('All Teams') }}</option>
          <option v-for="team in teams" :key="team" :value="team">
            {{ team }}
          </option>
        </select>
      </div>

      <div class="mb-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
        <div class="rounded-md border border-gray-200 bg-white p-4">
          <div class="text-xs uppercase tracking-wide text-gray-500">
            {{ __('Agents') }}
          </div>
          <div class="mt-1 text-2xl font-semibold text-gray-900">
            {{ totalAgents }}
          </div>
        </div>
        <div class="rounded-md border border-gray-200 bg-white p-4">
          <div class="text-xs uppercase tracking-wide text-gray-500">
            {{ __('Tickets Assigned') }}
          </div>
          <div class="mt-1 text-2xl font-semibold text-gray-900">
            {{ formatCount(totalTicketsAssigned) }}
          </div>
        </div>
        <div class="rounded-md border border-gray-200 bg-white p-4">
          <div class="text-xs uppercase tracking-wide text-gray-500">
            {{ __('Pending Tickets') }}
          </div>
          <div class="mt-1 text-2xl font-semibold text-gray-900">
            {{ formatCount(totalPendingTickets) }}
          </div>
        </div>
        <div class="rounded-md border border-gray-200 bg-white p-4">
          <div class="text-xs uppercase tracking-wide text-gray-500">
            {{ __('Avg Time to First Open') }}
          </div>
          <div class="mt-1 text-2xl font-semibold text-gray-900">
            {{ formatMinutes(avgFirstOpenMins) }}
          </div>
        </div>
        <div class="rounded-md border border-gray-200 bg-white p-4">
          <div class="text-xs uppercase tracking-wide text-gray-500">
            {{ __('Avg Time to Close') }}
          </div>
          <div class="mt-1 text-2xl font-semibold text-gray-900">
            {{ formatMinutes(avgTimeToCloseMins) }}
          </div>
        </div>
        <div class="rounded-md border border-gray-200 bg-white p-4">
          <div class="text-xs uppercase tracking-wide text-gray-500">
            {{ __('Top Agent') }}
          </div>
          <div class="mt-1 truncate text-base font-semibold text-gray-900">
            {{ topAgent?.agent_name || topAgent?.agent_email || '-' }}
          </div>
          <div class="mt-1 text-xs text-gray-500">
            {{ __('Tickets') }}:
            {{ formatCount(topAgent?.total_tickets_assigned || 0) }}
          </div>
        </div>
      </div>

      <div v-if="rows.length > 0" class="mb-4 grid gap-4 lg:grid-cols-2">
        <div class="rounded-md border border-gray-200 bg-white p-4">
          <div class="mb-3 text-sm font-medium text-gray-800">
            {{ __('Assigned vs Pending Tickets by Agent') }}
          </div>
          <div class="space-y-3">
            <div v-for="item in ticketsByAgent" :key="item.label">
              <div class="mb-1 truncate text-xs text-gray-600">{{ item.label }}</div>
              <div class="grid grid-cols-[140px_1fr] items-center gap-2 text-xs">
                <span class="text-gray-500">
                  {{ __('Assigned') }} {{ formatCount(item.assigned) }}
                </span>
                <div class="h-2 rounded bg-gray-100">
                  <div
                    class="h-2 rounded bg-blue-500"
                    :style="{ width: `${item.assignedWidth}%` }"
                  />
                </div>
              </div>
              <div class="mt-1 grid grid-cols-[140px_1fr] items-center gap-2 text-xs">
                <span class="text-gray-500">
                  {{ __('Pending') }} {{ formatCount(item.pending) }}
                </span>
                <div class="h-2 rounded bg-gray-100">
                  <div
                    class="h-2 rounded bg-amber-500"
                    :style="{ width: `${item.pendingWidth}%` }"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="rounded-md border border-gray-200 bg-white p-4">
          <div class="mb-3 text-sm font-medium text-gray-800">
            {{ __('Time to Close vs First Open Time (mins)') }}
          </div>
          <div class="space-y-3">
            <div v-for="item in timeByAgent" :key="item.label">
              <div class="mb-1 truncate text-xs text-gray-600">{{ item.label }}</div>
              <div class="grid grid-cols-[120px_1fr] items-center gap-2 text-xs">
                <span class="text-gray-500">{{ __('First Open') }} {{ formatMinutes(item.firstOpen) }}</span>
                <div class="h-2 rounded bg-gray-100">
                  <div class="h-2 rounded bg-indigo-500" :style="{ width: `${item.firstOpenWidth}%` }" />
                </div>
              </div>
              <div class="mt-1 grid grid-cols-[120px_1fr] items-center gap-2 text-xs">
                <span class="text-gray-500">{{ __('Close') }} {{ formatMinutes(item.close) }}</span>
                <div class="h-2 rounded bg-gray-100">
                  <div class="h-2 rounded bg-emerald-500" :style="{ width: `${item.closeWidth}%` }" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="overflow-hidden rounded-md border border-gray-200 bg-white">
        <table class="min-w-full text-sm">
          <thead class="bg-gray-50 text-left text-gray-600">
            <tr>
              <th class="px-4 py-2 font-medium">{{ __('Agent Name') }}</th>
              <th class="px-4 py-2 font-medium">{{ __('Email') }}</th>
              <th class="px-4 py-2 font-medium">{{ __('Tickets Assigned') }}</th>
              <th class="px-4 py-2 font-medium">{{ __('Pending Tickets') }}</th>
              <th class="px-4 py-2 font-medium">{{ __('Closed Tickets') }}</th>
              <th class="px-4 py-2 font-medium">{{ __('Avg Time to First Open (mins)') }}</th>
              <th class="px-4 py-2 font-medium">{{ __('Avg Time to Close (mins)') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td class="px-4 py-8 text-center text-gray-500" colspan="7">
                {{ __('Loading...') }}
              </td>
            </tr>
            <tr v-else-if="rows.length === 0">
              <td class="px-4 py-8 text-center text-gray-500" colspan="7">
                {{ __('No data available') }}
              </td>
            </tr>
            <tr
              v-else
              v-for="row in rows"
              :key="row.agent_email"
              class="border-t border-gray-100"
            >
              <td class="px-4 py-2 text-gray-900">{{ row.agent_name || '-' }}</td>
              <td class="px-4 py-2 text-gray-700">{{ row.agent_email || '-' }}</td>
              <td class="px-4 py-2 text-gray-900">{{ row.total_tickets_assigned || 0 }}</td>
              <td class="px-4 py-2 text-gray-900">{{ row.pending_tickets || 0 }}</td>
              <td class="px-4 py-2 text-gray-900">{{ row.closed_tickets || 0 }}</td>
              <td class="px-4 py-2 text-gray-700">{{ row.avg_first_open_time || '-' }}</td>
              <td class="px-4 py-2 text-gray-700">{{ row.avg_close_time || '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { __ } from '@/translation';
import { computed, onMounted, ref } from 'vue';

interface AgentPerformanceRow {
  agent_name: string;
  agent_email: string;
  total_tickets_assigned: number;
  pending_tickets: number;
  closed_tickets: number;
  avg_first_open_time: string;
  avg_close_time: string;
  avg_first_open_time_mins: number | null;
  avg_close_time_mins: number | null;
}

const selectedPeriod = ref('today');
const selectedTeam = ref('');
const teams = ref<string[]>([]);
const loading = ref(false);
const rows = ref<AgentPerformanceRow[]>([]);

const periodOptions = [
  { label: __('Today'), value: 'today' },
  { label: __('This Week'), value: 'week' },
  { label: __('This Month'), value: 'month' },
];

const totalAgents = computed(() => rows.value.length);
const totalTicketsAssigned = computed(() =>
  rows.value.reduce((sum, row) => sum + Number(row.total_tickets_assigned || 0), 0)
);
const totalPendingTickets = computed(() =>
  rows.value.reduce((sum, row) => sum + Number(row.pending_tickets || 0), 0)
);
const topAgent = computed(() =>
  [...rows.value].sort(
    (a, b) =>
      Number(b.total_tickets_assigned || 0) - Number(a.total_tickets_assigned || 0)
  )[0]
);
const avgFirstOpenMins = computed(() => averageMetric('avg_first_open_time_mins'));
const avgTimeToCloseMins = computed(() => averageMetric('avg_close_time_mins'));

const ticketsByAgent = computed(() => {
  const sorted = [...rows.value]
    .sort(
      (a, b) =>
        Number(b.total_tickets_assigned || 0) - Number(a.total_tickets_assigned || 0)
    )
    .slice(0, 8);
  const max = Math.max(
    1,
    ...sorted.flatMap((row) => [
      Number(row.total_tickets_assigned || 0),
      Number(row.pending_tickets || 0),
    ])
  );
  return sorted.map((row) => {
    const assigned = Number(row.total_tickets_assigned || 0);
    const pending = Number(row.pending_tickets || 0);
    return {
      label: row.agent_name || row.agent_email || '-',
      assigned,
      pending,
      assignedWidth: (assigned / max) * 100,
      pendingWidth: (pending / max) * 100,
    };
  });
});

const timeByAgent = computed(() => {
  const sorted = [...rows.value]
    .sort(
      (a, b) =>
        Number(b.total_tickets_assigned || 0) - Number(a.total_tickets_assigned || 0)
    )
    .slice(0, 6);
  const max = Math.max(
    1,
    ...sorted.flatMap((row) => [
      Number(row.avg_first_open_time_mins || 0),
      Number(row.avg_close_time_mins || 0),
    ])
  );
  return sorted.map((row) => {
    const firstOpen = row.avg_first_open_time_mins;
    const close = row.avg_close_time_mins;
    const firstOpenValue = Number(firstOpen || 0);
    const closeValue = Number(close || 0);
    return {
      label: row.agent_name || row.agent_email || '-',
      firstOpen,
      close,
      firstOpenWidth: (firstOpenValue / max) * 100,
      closeWidth: (closeValue / max) * 100,
    };
  });
});

async function fetchTeams() {
  try {
    const response = await fetch('/api/resource/HD Team?fields=["name"]', {
      credentials: 'include',
    });
    const data = await response.json();
    teams.value = (data?.data || []).map((d: { name: string }) => d.name);
  } catch (error) {
    teams.value = [];
  }
}

async function fetchData() {
  loading.value = true;
  try {
    const query = new URLSearchParams({ period: selectedPeriod.value });
    if (selectedTeam.value) {
      query.set('team', selectedTeam.value);
    }
    const response = await fetch(
      `/api/method/get_agent_performance?${query.toString()}`,
      {
        credentials: 'include',
      }
    );
    const data = await response.json();
    const message = data?.message;
    const rawRows = Array.isArray(message)
      ? message
      : message?.agent_performance || [];

    rows.value = rawRows.map((row: Record<string, unknown>) => {
      const avgFirstOpenTime = String(row.avg_first_open_time || '-');
      const avgCloseTime = String(row.avg_close_time || '-');
      return {
        agent_name: String(row.agent_name || ''),
        agent_email: String(row.agent_email || ''),
        total_tickets_assigned: Number(row.total_tickets_assigned || 0),
        pending_tickets: Number(row.pending_tickets || 0),
        closed_tickets: Number(row.closed_tickets || 0),
        avg_first_open_time: avgFirstOpenTime,
        avg_close_time: avgCloseTime,
        avg_first_open_time_mins: toMinutesNumber(
          row.avg_first_open_time_mins,
          avgFirstOpenTime
        ),
        avg_close_time_mins: toMinutesNumber(
          row.avg_close_time_mins,
          avgCloseTime
        ),
      };
    });
  } catch (error) {
    rows.value = [];
  } finally {
    loading.value = false;
  }
}

function setPeriod(period: string) {
  if (selectedPeriod.value === period) return;
  selectedPeriod.value = period;
  fetchData();
}

function formatMinutes(value: number | null) {
  if (value === null || value === undefined) return '-';
  return `${Number(value).toFixed(2)} min`;
}

function formatCount(value: number) {
  return Number(value || 0).toLocaleString();
}

function averageMetric(
  key: 'avg_first_open_time_mins' | 'avg_close_time_mins'
) {
  const values = rows.value
    .map((row) => row[key])
    .filter((value): value is number => value !== null && value !== undefined);
  if (!values.length) return null;
  return values.reduce((sum, value) => sum + Number(value), 0) / values.length;
}

function toMinutesNumber(
  numericValue: unknown,
  stringValue: string
) {
  if (typeof numericValue === 'number') return numericValue;
  if (typeof numericValue === 'string') {
    const parsedNumeric = Number(numericValue);
    if (!Number.isNaN(parsedNumeric)) return parsedNumeric;
  }

  const parsedText = Number.parseFloat(
    String(stringValue || '').replace(' min', '').trim()
  );
  if (Number.isNaN(parsedText)) return null;
  return parsedText;
}

onMounted(async () => {
  await fetchTeams();
  await fetchData();
});
</script>