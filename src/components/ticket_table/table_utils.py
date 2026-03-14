"""Table Utils"""

from __future__ import annotations

from nicegui import ui
from nicegui.elements.table import Table


def add_expandable_row(table: Table) -> Table:
    """Make the table expandable

    Args:
        table (Table): The table instance to make expandable
    """
    table.add_slot(
        "header",
        r"""
            <q-tr :props="props">
                <q-th auto-width v-if="props.selected !== void 0">
                    <q-checkbox v-model="props.selected" dense />
                </q-th>
                <q-th auto-width />
                <q-th v-for="col in props.cols" :key="col.name" :props="props">
                    {{ col.label }}
                </q-th>
            </q-tr>
        """,
    )

    table.add_slot(
        "body",
        r"""
            <q-tr :props="props">
                <q-td auto-width v-if="props.selected !== void 0">
                    <q-checkbox v-model="props.selected" dense />
                </q-td>
                <q-td auto-width>
                    <q-btn size="sm" color="accent" round dense
                        @click="props.expand = !props.expand"
                        :icon="props.expand ? 'remove' : 'add'" />
                </q-td>
                <template v-for="col in props.cols" :key="col.name">
                    <q-td v-if="col.name === 'status'" :props="props" :key="col.name">
                        <q-badge :color="props.row.status_color">
                            {{ col.value }}
                        </q-badge>
                    </q-td>
                    <q-td v-else-if="col.name === 'priority'" :props="props" :key="col.name">
                        <q-badge :color="props.row.priority_color">
                            {{ col.value }}
                        </q-badge>
                    </q-td>
                    <q-td v-else-if="col.name === 'triage'" :props="props" :key="col.name">
                        <q-btn
                            flat
                            color="secondary"
                            no-caps
                            :label="props.row.triage"
                            :disable="!['Open', 'Pending'].includes(props.row.status)"
                            @click.stop="$parent.$emit('ticket-triage', props.row)"
                        />
                    </q-td>
                    <q-td v-else-if="col.name === 'close'" :props="props" :key="col.name">
                        <q-btn
                            flat
                            color="negative"
                            no-caps
                            :label="props.row.close"
                            :disable="props.row.status !== 'Open'"
                            @click.stop="$parent.$emit('ticket-close', props.row)"
                        />
                    </q-td>
                    <q-td v-else :props="props" :key="col.name">
                        {{ col.value }}
                    </q-td>
                </template>
            </q-tr>
            <q-tr v-show="props.expand" :props="props">
                <q-td colspan="100%">
                    <div class="q-pa-md row items-start q-gutter-md">
                        <q-card class="my-card" flat bordered>
                            <q-item>
                                <q-item-section>
                                    <q-item-label>Detailed Overview</q-item-label>
                                    <q-item-label caption>
                                        Detailed overview of the ticket
                                    </q-item-label>
                                </q-item-section>
                            </q-item>
                            <q-separator />
                            <q-card-section horizontal>
                                <q-card-section auto-width>
                                    <div class="text-subtitle2">Original Ticket</div>
                                    <div>{{ props.row.description }}</div>
                                </q-card-section>
                                <q-separator vertical />
                                <q-card-section>
                                    <div class="row items-start q-col-gutter-md">
                                        <div class="col-12 col-md-6">
                                            <q-item>
                                                <q-item-section>
                                                    <q-item-label>Manual Triage</q-item-label>
                                                    <div v-if="props.row.manual_summary || props.row.manual_response || (props.row.manual_next_steps && props.row.manual_next_steps.length)">
                                                        <div class="text-caption q-mt-sm">Summary</div>
                                                        <q-item-label caption>{{ props.row.manual_summary || 'Not provided' }}</q-item-label>
                                                        <q-separator spaced inset />
                                                        <div class="text-caption q-mt-sm">Response</div>
                                                        <q-item-label caption>{{ props.row.manual_response || 'Not provided' }}</q-item-label>
                                                        <q-separator spaced inset />
                                                        <div class="text-caption q-mt-sm">Next Steps</div>
                                                        <q-list v-if="props.row.manual_next_steps && props.row.manual_next_steps.length" bordered separator>
                                                            <q-item v-for="step in props.row.manual_next_steps" :key="'manual-' + step" clickable v-ripple>
                                                                {{ step }}
                                                            </q-item>
                                                        </q-list>
                                                        <q-item-label v-else caption>No manual next steps recorded.</q-item-label>
                                                    </div>
                                                    <q-item-label v-else caption>No manual triage saved for this ticket yet.</q-item-label>
                                                </q-item-section>
                                            </q-item>
                                        </div>
                                        <div class="col-12 col-md-6">
                                            <q-item>
                                                <q-item-section>
                                                    <q-item-label>AI Triage</q-item-label>
                                                    <div v-if="props.row.ai_summary || props.row.ai_recommended_action || props.row.ai_reasoning">
                                                        <div class="text-caption q-mt-sm">Summary</div>
                                                        <q-item-label caption>{{ props.row.ai_summary || 'Not provided' }}</q-item-label>
                                                        <q-separator spaced inset />
                                                        <div class="text-caption q-mt-sm">Recommended Action</div>
                                                        <q-item-label caption>{{ props.row.ai_recommended_action || 'Not provided' }}</q-item-label>
                                                        <q-separator spaced inset />
                                                        <div class="text-caption q-mt-sm">Department</div>
                                                        <q-item-label caption>{{ props.row.department || 'Not assigned' }}</q-item-label>
                                                        <q-separator spaced inset />
                                                        <div class="text-caption q-mt-sm">Confidence</div>
                                                        <q-item-label caption>{{ props.row.ai_confidence || 'Not provided' }}</q-item-label>
                                                        <q-separator spaced inset />
                                                        <div class="text-caption q-mt-sm">Missing Information</div>
                                                        <q-item-label caption>{{ props.row.ai_missing_information || 'Not provided' }}</q-item-label>
                                                        <q-separator spaced inset />
                                                        <div class="text-caption q-mt-sm">Reasoning</div>
                                                        <q-item-label caption>{{ props.row.ai_reasoning || 'Not provided' }}</q-item-label>
                                                        <q-separator spaced inset />
                                                        <div class="text-caption q-mt-sm">Processing Time</div>
                                                        <q-item-label caption>{{ props.row.ai_processing_ms ? (props.row.ai_processing_ms / 1000).toFixed(2) + ' seconds' : 'Not recorded' }}</q-item-label>
                                                    </div>
                                                    <q-item-label v-else caption>No AI triage saved for this ticket yet.</q-item-label>
                                                </q-item-section>
                                            </q-item>
                                        </div>
                                    </div>
                                    <q-separator spaced inset />
                                    <q-item>
                                        <q-item-section>
                                            <q-item-label>Retrieved Context</q-item-label>
                                            <div v-if="props.row.ai_trace">
                                                <div class="text-caption text-weight-medium q-mt-sm">Knowledge Base Matches</div>
                                                <q-list dense bordered separator>
                                                    <q-item v-for="match in props.row.ai_trace.kb_matches" :key="'kb-' + match.id">
                                                        <q-item-section>
                                                            <q-item-label>{{ match.source_name }} ({{ Number(match.similarity).toFixed(3) }})</q-item-label>
                                                            <q-item-label caption>{{ match.chunk_text }}</q-item-label>
                                                        </q-item-section>
                                                    </q-item>
                                                </q-list>
                                                <div class="text-caption text-weight-medium q-mt-md">Similar Tickets</div>
                                                <q-list dense bordered separator>
                                                    <q-item v-for="match in props.row.ai_trace.ticket_matches" :key="'ticket-' + match.ticket_id">
                                                        <q-item-section>
                                                            <q-item-label>#{{ match.ticket_id }} {{ match.title }} ({{ Number(match.similarity).toFixed(3) }})</q-item-label>
                                                            <q-item-label caption>{{ match.combined_text }}</q-item-label>
                                                        </q-item-section>
                                                    </q-item>
                                                </q-list>
                                            </div>
                                            <q-item-label v-else caption>No AI trace available for this ticket yet.</q-item-label>
                                        </q-item-section>
                                    </q-item>
                                </q-card-section>
                            </q-card-section>
                        </q-card>
                    </div>
                </q-td>
            </q-tr>
        """,
    )

    return table


def add_search(table: Table) -> Table:
    """Add Search to the table

    Args:
        table (Table): The table instance to add search to

    Returns: Table
    """
    with table.add_slot("top-right"):
        with ui.input(placeholder="Search").props("type=search").bind_value(table, "filter").add_slot("append"):
            ui.icon("search")
    return table
