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
                    <q-td v-else-if="col.name === 'start'" :props="props" :key="col.name">
                        <q-btn
                            flat
                            color="primary"
                            no-caps
                            :label="props.row.start"
                            :disable="props.row.status !== 'Open'"
                            @click.stop="$parent.$emit('ticket-start', props.row)"
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
                                    <q-item>
                                        <q-item-section auto-width>
                                            <q-item-label>AI Summary</q-item-label>
                                            <q-item-label caption>{{props.row.ai_summary}}</q-item-label>
                                        </q-item-section>  
                                    </q-item>
                                    <q-separator spaced inset />
                                    <q-item>
                                        <q-item-section>
                                            <q-item-label>AI Response</q-item-label>
                                            <q-item-label caption >{{props.row.ai_response }}</q-item-label>
                                        </q-item-section>  
                                     </q-item>
                                    <q-separator spaced inset />
                                    <q-item>
                                        <q-item-section>
                                            <q-item-label>AI Confidence</q-item-label>
                                            <q-item-label caption >{{props.row.ai_confidence }}</q-item-label>
                                        </q-item-section>  
                                     </q-item>
                                    <q-separator spaced inset />
                                    <q-item>
                                        <q-item-section>
                                            <q-item-label>AI Category</q-item-label>
                                            <q-item-label caption >{{props.row.category }}</q-item-label>
                                        </q-item-section>  
                                    </q-item>
                                    <q-separator spaced inset />
                                    <q-item>
                                        <q-item-section>
                                            <q-item-label>AI Next Steps</q-item-label>
                                            <q-list bordered separator>
                                                <q-item v-for="step in props.row.ai_next_steps" :props="props" :key="step" clickable v-ripple>
                                                    {{step}}
                                                </q-item>
                                            </q-list>
                                        </q-item-section>  
                                    </q-item>
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
