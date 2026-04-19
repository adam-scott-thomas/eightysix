import { useState } from 'react';
import {
  Database,
  Users,
  UtensilsCrossed,
  ShoppingCart,
  Clock,
  Send,
  Eraser,
  FileText,
  Loader2,
  CheckCircle,
  AlertTriangle,
  MapPin,
  Plus,
  ChevronDown,
  Trash2,
} from 'lucide-react';
import { useStore } from '../hooks/useStore';
import * as api from '../lib/api';

/* ------------------------------------------------------------------ */
/*  Tab definitions                                                    */
/* ------------------------------------------------------------------ */

type TabId = 'employees' | 'menu' | 'orders' | 'shifts';

interface TabDef {
  id: TabId;
  label: string;
  icon: typeof Database;
  placeholder: string;
  template: string;
}

const TABS: TabDef[] = [
  {
    id: 'employees',
    label: 'Employees',
    icon: Users,
    placeholder: `[
  {
    "external_employee_id": "E001",
    "first_name": "Maria",
    "last_name": "Garcia",
    "role": "floor",
    "hourly_rate": 16.50
  }
]`,
    template: JSON.stringify(
      [
        {
          external_employee_id: 'E001',
          first_name: 'Maria',
          last_name: 'Garcia',
          role: 'floor',
          hourly_rate: 16.5,
        },
        {
          external_employee_id: 'E002',
          first_name: 'James',
          last_name: 'Chen',
          role: 'kitchen',
          hourly_rate: 18.0,
        },
      ],
      null,
      2,
    ),
  },
  {
    id: 'menu',
    label: 'Menu Items',
    icon: UtensilsCrossed,
    placeholder: `[
  {
    "external_item_id": "M001",
    "item_name": "Classic Burger",
    "category": "entrees",
    "price": 13.00,
    "estimated_food_cost": 4.50
  }
]`,
    template: JSON.stringify(
      [
        {
          external_item_id: 'M001',
          item_name: 'Classic Burger',
          category: 'entrees',
          price: 13.0,
          estimated_food_cost: 4.5,
        },
        {
          external_item_id: 'M002',
          item_name: 'Caesar Salad',
          category: 'salads',
          price: 10.0,
          estimated_food_cost: 3.0,
        },
        {
          external_item_id: 'M003',
          item_name: 'Fries',
          category: 'sides',
          price: 5.0,
          estimated_food_cost: 1.25,
        },
      ],
      null,
      2,
    ),
  },
  {
    id: 'orders',
    label: 'Orders',
    icon: ShoppingCart,
    placeholder: `[
  {
    "external_order_id": "ORD-001",
    "employee_external_id": "E001",
    "ordered_at": "2025-03-15T14:30:00Z",
    "order_total": 18.00,
    "channel": "dine_in",
    "items": [
      { "external_item_id": "M001", "quantity": 1, "line_total": 13.00 },
      { "external_item_id": "M003", "quantity": 1, "line_total": 5.00 }
    ]
  }
]`,
    template: JSON.stringify(
      [
        {
          external_order_id: 'ORD-001',
          employee_external_id: 'E001',
          ordered_at: '2025-03-15T14:30:00Z',
          order_total: 18.0,
          channel: 'dine_in',
          items: [
            { external_item_id: 'M001', quantity: 1, line_total: 13.0 },
            { external_item_id: 'M003', quantity: 1, line_total: 5.0 },
          ],
        },
        {
          external_order_id: 'ORD-002',
          employee_external_id: 'E002',
          ordered_at: '2025-03-15T15:00:00Z',
          order_total: 10.0,
          channel: 'takeout',
          items: [
            { external_item_id: 'M002', quantity: 1, line_total: 10.0 },
          ],
        },
      ],
      null,
      2,
    ),
  },
  {
    id: 'shifts',
    label: 'Shifts',
    icon: Clock,
    placeholder: `[
  {
    "employee_external_id": "E001",
    "clock_in": "2025-03-15T10:00:00Z",
    "clock_out": null,
    "role_during_shift": "floor",
    "source_type": "manual"
  }
]`,
    template: JSON.stringify(
      [
        {
          employee_external_id: 'E001',
          clock_in: '2025-03-15T10:00:00Z',
          clock_out: '2025-03-15T18:00:00Z',
          role_during_shift: 'floor',
          source_type: 'manual',
        },
        {
          employee_external_id: 'E002',
          clock_in: '2025-03-15T11:00:00Z',
          clock_out: null,
          role_during_shift: 'kitchen',
          source_type: 'manual',
        },
      ],
      null,
      2,
    ),
  },
];

const TIMEZONES = [
  'America/New_York',
  'America/Chicago',
  'America/Denver',
  'America/Los_Angeles',
  'America/Phoenix',
  'America/Anchorage',
  'Pacific/Honolulu',
  'US/Eastern',
  'US/Central',
  'US/Mountain',
  'US/Pacific',
  'UTC',
];

/* ------------------------------------------------------------------ */
/*  Form Components                                                    */
/* ------------------------------------------------------------------ */

interface EmployeeRow {
  external_employee_id: string;
  first_name: string;
  last_name: string;
  role: string;
  hourly_rate: string;
}

function EmployeeForm({ onSubmit }: { onSubmit: (data: unknown[]) => void }) {
  const [rows, setRows] = useState<EmployeeRow[]>([
    { external_employee_id: '', first_name: '', last_name: '', role: 'floor', hourly_rate: '' },
  ]);

  const addRow = () =>
    setRows([...rows, { external_employee_id: '', first_name: '', last_name: '', role: 'floor', hourly_rate: '' }]);

  const removeRow = (i: number) => setRows(rows.filter((_, idx) => idx !== i));

  const updateRow = (i: number, field: keyof EmployeeRow, value: string) => {
    const updated = [...rows];
    updated[i] = { ...updated[i], [field]: value };
    setRows(updated);
  };

  const handleSubmit = () => {
    const data = rows
      .filter((r) => r.external_employee_id && r.first_name)
      .map((r) => ({
        ...r,
        hourly_rate: r.hourly_rate ? parseFloat(r.hourly_rate) : null,
      }));
    if (data.length > 0) onSubmit(data);
  };

  return (
    <div className="space-y-3">
      {rows.map((row, i) => (
        <div key={i} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-[1fr_1fr_1fr_auto_auto_auto] gap-2 items-center border border-gray-100 sm:border-0 rounded-lg sm:rounded-none p-3 sm:p-0">
          <input
            placeholder="ID (e.g. E001)"
            value={row.external_employee_id}
            onChange={(e) => updateRow(i, 'external_employee_id', e.target.value)}
            className="input-field"
          />
          <input
            placeholder="First name"
            value={row.first_name}
            onChange={(e) => updateRow(i, 'first_name', e.target.value)}
            className="input-field"
          />
          <input
            placeholder="Last name"
            value={row.last_name}
            onChange={(e) => updateRow(i, 'last_name', e.target.value)}
            className="input-field"
          />
          <select
            value={row.role}
            onChange={(e) => updateRow(i, 'role', e.target.value)}
            className="input-field"
          >
            <option value="floor">Floor</option>
            <option value="kitchen">Kitchen</option>
            <option value="bar">Bar</option>
            <option value="manager">Manager</option>
          </select>
          <input
            type="number"
            step="0.01"
            placeholder="$/hr"
            value={row.hourly_rate}
            onChange={(e) => updateRow(i, 'hourly_rate', e.target.value)}
            className="input-field w-full lg:w-24"
          />
          {rows.length > 1 && (
            <button
              onClick={() => removeRow(i)}
              className="p-2 text-gray-400 hover:text-red-500 transition-colors justify-self-end sm:justify-self-auto"
              title="Remove row"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      ))}
      <div className="flex gap-2">
        <button onClick={addRow} className="text-sm text-blue-600 hover:text-blue-800">
          + Add row
        </button>
        <button
          onClick={handleSubmit}
          className="ml-auto px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700"
        >
          Submit
        </button>
      </div>
    </div>
  );
}

interface MenuItemRow {
  external_item_id: string;
  item_name: string;
  category: string;
  price: string;
  estimated_food_cost: string;
}

function MenuItemForm({ onSubmit }: { onSubmit: (data: unknown[]) => void }) {
  const [rows, setRows] = useState<MenuItemRow[]>([
    { external_item_id: '', item_name: '', category: 'entrees', price: '', estimated_food_cost: '' },
  ]);

  const addRow = () =>
    setRows([
      ...rows,
      { external_item_id: '', item_name: '', category: 'entrees', price: '', estimated_food_cost: '' },
    ]);

  const removeRow = (i: number) => setRows(rows.filter((_, idx) => idx !== i));

  const updateRow = (i: number, field: keyof MenuItemRow, value: string) => {
    const updated = [...rows];
    updated[i] = { ...updated[i], [field]: value };
    setRows(updated);
  };

  const handleSubmit = () => {
    const data = rows
      .filter((r) => r.external_item_id && r.item_name)
      .map((r) => ({
        external_item_id: r.external_item_id,
        item_name: r.item_name,
        category: r.category,
        price: r.price ? parseFloat(r.price) : null,
        estimated_food_cost: r.estimated_food_cost ? parseFloat(r.estimated_food_cost) : null,
      }));
    if (data.length > 0) onSubmit(data);
  };

  return (
    <div className="space-y-3">
      {rows.map((row, i) => (
        <div key={i} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-[1fr_1.5fr_auto_auto_auto_auto] gap-2 items-center border border-gray-100 sm:border-0 rounded-lg sm:rounded-none p-3 sm:p-0">
          <input
            placeholder="ID (e.g. M001)"
            value={row.external_item_id}
            onChange={(e) => updateRow(i, 'external_item_id', e.target.value)}
            className="input-field"
          />
          <input
            placeholder="Item name"
            value={row.item_name}
            onChange={(e) => updateRow(i, 'item_name', e.target.value)}
            className="input-field"
          />
          <select
            value={row.category}
            onChange={(e) => updateRow(i, 'category', e.target.value)}
            className="input-field"
          >
            <option value="entrees">Entrees</option>
            <option value="appetizers">Appetizers</option>
            <option value="salads">Salads</option>
            <option value="sides">Sides</option>
            <option value="desserts">Desserts</option>
            <option value="beverages">Beverages</option>
          </select>
          <input
            type="number"
            step="0.01"
            placeholder="Price"
            value={row.price}
            onChange={(e) => updateRow(i, 'price', e.target.value)}
            className="input-field w-full lg:w-24"
          />
          <input
            type="number"
            step="0.01"
            placeholder="Food cost"
            value={row.estimated_food_cost}
            onChange={(e) => updateRow(i, 'estimated_food_cost', e.target.value)}
            className="input-field w-full lg:w-24"
          />
          {rows.length > 1 && (
            <button
              onClick={() => removeRow(i)}
              className="p-2 text-gray-400 hover:text-red-500 transition-colors justify-self-end sm:justify-self-auto"
              title="Remove row"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      ))}
      <div className="flex gap-2">
        <button onClick={addRow} className="text-sm text-blue-600 hover:text-blue-800">
          + Add row
        </button>
        <button
          onClick={handleSubmit}
          className="ml-auto px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700"
        >
          Submit
        </button>
      </div>
    </div>
  );
}

interface OrderItemRow {
  external_item_id: string;
  quantity: string;
  line_total: string;
}

interface OrderRow {
  external_order_id: string;
  employee_external_id: string;
  ordered_at: string;
  order_total: string;
  channel: string;
  items: OrderItemRow[];
}

function OrderForm({ onSubmit }: { onSubmit: (data: unknown[]) => void }) {
  const [rows, setRows] = useState<OrderRow[]>([
    {
      external_order_id: '',
      employee_external_id: '',
      ordered_at: '',
      order_total: '',
      channel: 'dine_in',
      items: [{ external_item_id: '', quantity: '1', line_total: '' }],
    },
  ]);

  const addRow = () =>
    setRows([
      ...rows,
      {
        external_order_id: '',
        employee_external_id: '',
        ordered_at: '',
        order_total: '',
        channel: 'dine_in',
        items: [{ external_item_id: '', quantity: '1', line_total: '' }],
      },
    ]);

  const removeRow = (i: number) => setRows(rows.filter((_, idx) => idx !== i));

  const updateRow = (i: number, field: keyof Omit<OrderRow, 'items'>, value: string) => {
    const updated = [...rows];
    updated[i] = { ...updated[i], [field]: value };
    setRows(updated);
  };

  const addOrderItem = (orderIdx: number) => {
    const updated = [...rows];
    updated[orderIdx] = {
      ...updated[orderIdx],
      items: [...updated[orderIdx].items, { external_item_id: '', quantity: '1', line_total: '' }],
    };
    setRows(updated);
  };

  const updateOrderItem = (orderIdx: number, itemIdx: number, field: keyof OrderItemRow, value: string) => {
    const updated = [...rows];
    const items = [...updated[orderIdx].items];
    items[itemIdx] = { ...items[itemIdx], [field]: value };
    updated[orderIdx] = { ...updated[orderIdx], items };
    setRows(updated);
  };

  const removeOrderItem = (orderIdx: number, itemIdx: number) => {
    const updated = [...rows];
    updated[orderIdx] = {
      ...updated[orderIdx],
      items: updated[orderIdx].items.filter((_, idx) => idx !== itemIdx),
    };
    setRows(updated);
  };

  const handleSubmit = () => {
    const data = rows
      .filter((r) => r.external_order_id)
      .map((r) => ({
        external_order_id: r.external_order_id,
        employee_external_id: r.employee_external_id || null,
        ordered_at: r.ordered_at || new Date().toISOString(),
        order_total: r.order_total ? parseFloat(r.order_total) : 0,
        channel: r.channel,
        items: r.items
          .filter((it) => it.external_item_id)
          .map((it) => ({
            external_item_id: it.external_item_id,
            quantity: it.quantity ? parseInt(it.quantity, 10) : 1,
            line_total: it.line_total ? parseFloat(it.line_total) : 0,
          })),
      }));
    if (data.length > 0) onSubmit(data);
  };

  return (
    <div className="space-y-4">
      {rows.map((row, i) => (
        <div key={i} className="border border-gray-200 rounded-lg p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-gray-500 uppercase">Order {i + 1}</span>
            {rows.length > 1 && (
              <button
                onClick={() => removeRow(i)}
                className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                title="Remove order"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2">
            <input
              placeholder="Order ID (e.g. ORD-001)"
              value={row.external_order_id}
              onChange={(e) => updateRow(i, 'external_order_id', e.target.value)}
              className="input-field"
            />
            <input
              placeholder="Employee ID"
              value={row.employee_external_id}
              onChange={(e) => updateRow(i, 'employee_external_id', e.target.value)}
              className="input-field"
            />
            <input
              type="datetime-local"
              value={row.ordered_at}
              onChange={(e) => updateRow(i, 'ordered_at', e.target.value)}
              className="input-field"
            />
            <input
              type="number"
              step="0.01"
              placeholder="Total"
              value={row.order_total}
              onChange={(e) => updateRow(i, 'order_total', e.target.value)}
              className="input-field"
            />
            <select
              value={row.channel}
              onChange={(e) => updateRow(i, 'channel', e.target.value)}
              className="input-field"
            >
              <option value="dine_in">Dine In</option>
              <option value="takeout">Takeout</option>
              <option value="delivery">Delivery</option>
              <option value="drive_through">Drive Through</option>
            </select>
          </div>
          {/* Order line items */}
          <div className="ml-4 space-y-2">
            <span className="text-xs font-medium text-gray-400 uppercase">Line Items</span>
            {row.items.map((item, j) => (
              <div key={j} className="grid grid-cols-[1fr_auto_auto] sm:grid-cols-[1.5fr_auto_auto_auto] gap-2 items-center">
                <input
                  placeholder="Item ID (e.g. M001)"
                  value={item.external_item_id}
                  onChange={(e) => updateOrderItem(i, j, 'external_item_id', e.target.value)}
                  className="input-field"
                />
                <input
                  type="number"
                  min="1"
                  placeholder="Qty"
                  value={item.quantity}
                  onChange={(e) => updateOrderItem(i, j, 'quantity', e.target.value)}
                  className="input-field w-16 sm:w-20"
                />
                <input
                  type="number"
                  step="0.01"
                  placeholder="Line total"
                  value={item.line_total}
                  onChange={(e) => updateOrderItem(i, j, 'line_total', e.target.value)}
                  className="input-field w-20 sm:w-28"
                />
                {row.items.length > 1 && (
                  <button
                    onClick={() => removeOrderItem(i, j)}
                    className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            ))}
            <button
              onClick={() => addOrderItem(i)}
              className="text-xs text-blue-600 hover:text-blue-800"
            >
              + Add line item
            </button>
          </div>
        </div>
      ))}
      <div className="flex gap-2">
        <button onClick={addRow} className="text-sm text-blue-600 hover:text-blue-800">
          + Add order
        </button>
        <button
          onClick={handleSubmit}
          className="ml-auto px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700"
        >
          Submit
        </button>
      </div>
    </div>
  );
}

interface ShiftRow {
  employee_external_id: string;
  clock_in: string;
  clock_out: string;
  role_during_shift: string;
  source_type: string;
}

function ShiftForm({ onSubmit }: { onSubmit: (data: unknown[]) => void }) {
  const [rows, setRows] = useState<ShiftRow[]>([
    { employee_external_id: '', clock_in: '', clock_out: '', role_during_shift: 'floor', source_type: 'manual' },
  ]);

  const addRow = () =>
    setRows([
      ...rows,
      { employee_external_id: '', clock_in: '', clock_out: '', role_during_shift: 'floor', source_type: 'manual' },
    ]);

  const removeRow = (i: number) => setRows(rows.filter((_, idx) => idx !== i));

  const updateRow = (i: number, field: keyof ShiftRow, value: string) => {
    const updated = [...rows];
    updated[i] = { ...updated[i], [field]: value };
    setRows(updated);
  };

  const handleSubmit = () => {
    const data = rows
      .filter((r) => r.employee_external_id && r.clock_in)
      .map((r) => ({
        employee_external_id: r.employee_external_id,
        clock_in: r.clock_in ? new Date(r.clock_in).toISOString() : null,
        clock_out: r.clock_out ? new Date(r.clock_out).toISOString() : null,
        role_during_shift: r.role_during_shift,
        source_type: r.source_type,
      }));
    if (data.length > 0) onSubmit(data);
  };

  return (
    <div className="space-y-3">
      {rows.map((row, i) => (
        <div key={i} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-[1fr_1fr_1fr_auto_auto_auto] gap-2 items-center border border-gray-100 sm:border-0 rounded-lg sm:rounded-none p-3 sm:p-0">
          <input
            placeholder="Employee ID (e.g. E001)"
            value={row.employee_external_id}
            onChange={(e) => updateRow(i, 'employee_external_id', e.target.value)}
            className="input-field"
          />
          <input
            type="datetime-local"
            placeholder="Clock in"
            value={row.clock_in}
            onChange={(e) => updateRow(i, 'clock_in', e.target.value)}
            className="input-field"
          />
          <input
            type="datetime-local"
            placeholder="Clock out"
            value={row.clock_out}
            onChange={(e) => updateRow(i, 'clock_out', e.target.value)}
            className="input-field"
          />
          <select
            value={row.role_during_shift}
            onChange={(e) => updateRow(i, 'role_during_shift', e.target.value)}
            className="input-field"
          >
            <option value="floor">Floor</option>
            <option value="kitchen">Kitchen</option>
            <option value="bar">Bar</option>
            <option value="manager">Manager</option>
          </select>
          <select
            value={row.source_type}
            onChange={(e) => updateRow(i, 'source_type', e.target.value)}
            className="input-field"
          >
            <option value="manual">Manual</option>
            <option value="pos">POS</option>
            <option value="biometric">Biometric</option>
          </select>
          {rows.length > 1 && (
            <button
              onClick={() => removeRow(i)}
              className="p-2 text-gray-400 hover:text-red-500 transition-colors justify-self-end sm:justify-self-auto"
              title="Remove row"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      ))}
      <div className="flex gap-2">
        <button onClick={addRow} className="text-sm text-blue-600 hover:text-blue-800">
          + Add row
        </button>
        <button
          onClick={handleSubmit}
          className="ml-auto px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700"
        >
          Submit
        </button>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Input Mode Toggle                                                  */
/* ------------------------------------------------------------------ */

function InputModeToggle({
  mode,
  onChange,
}: {
  mode: 'form' | 'json';
  onChange: (mode: 'form' | 'json') => void;
}) {
  return (
    <div className="flex gap-1 bg-gray-100 rounded-lg p-0.5 w-fit">
      <button
        onClick={() => onChange('form')}
        className={`px-3 py-1 rounded-md text-xs font-medium transition-colors duration-150 cursor-pointer ${
          mode === 'form'
            ? 'bg-white text-gray-900 shadow-sm'
            : 'text-gray-500 hover:text-gray-700'
        }`}
      >
        Form
      </button>
      <button
        onClick={() => onChange('json')}
        className={`px-3 py-1 rounded-md text-xs font-medium transition-colors duration-150 cursor-pointer ${
          mode === 'json'
            ? 'bg-white text-gray-900 shadow-sm'
            : 'text-gray-500 hover:text-gray-700'
        }`}
      >
        JSON
      </button>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export function DataInputPage() {
  const store = useStore();

  const [activeTab, setActiveTab] = useState<TabId>('employees');
  const [inputMode, setInputMode] = useState<'form' | 'json'>('form');
  const [jsonValues, setJsonValues] = useState<Record<TabId, string>>({
    employees: '',
    menu: '',
    orders: '',
    shifts: '',
  });
  const [parseErrors, setParseErrors] = useState<Record<TabId, string | null>>({
    employees: null,
    menu: null,
    orders: null,
    shifts: null,
  });
  const [submitState, setSubmitState] = useState<
    Record<TabId, { status: 'idle' | 'loading' | 'success' | 'error'; message?: string }>
  >({
    employees: { status: 'idle' },
    menu: { status: 'idle' },
    orders: { status: 'idle' },
    shifts: { status: 'idle' },
  });

  // Location creation state
  const [showCreateLocation, setShowCreateLocation] = useState(false);
  const [newLocationName, setNewLocationName] = useState('');
  const [newLocationTimezone, setNewLocationTimezone] = useState('America/New_York');
  const [locationLoading, setLocationLoading] = useState(false);
  const [locationError, setLocationError] = useState<string | null>(null);

  const activeLocation = store.locations.find(
    (l) => l.id === store.activeLocationId,
  );
  const hasLocations = store.locations.length > 0;

  /* ---------- JSON helpers ---------- */

  function handleJsonChange(tab: TabId, value: string) {
    setJsonValues((prev) => ({ ...prev, [tab]: value }));
    // Clear parse error on edit
    if (parseErrors[tab]) {
      setParseErrors((prev) => ({ ...prev, [tab]: null }));
    }
  }

  function validateJson(tab: TabId): unknown[] | null {
    const raw = jsonValues[tab].trim();
    if (!raw) {
      setParseErrors((prev) => ({ ...prev, [tab]: 'JSON input is empty.' }));
      return null;
    }
    try {
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed)) {
        setParseErrors((prev) => ({
          ...prev,
          [tab]: 'Input must be a JSON array (wrap in [ ]).',
        }));
        return null;
      }
      setParseErrors((prev) => ({ ...prev, [tab]: null }));
      return parsed;
    } catch (e: unknown) {
      const msg = e instanceof SyntaxError ? e.message : 'Invalid JSON';
      setParseErrors((prev) => ({ ...prev, [tab]: msg }));
      return null;
    }
  }

  function loadTemplate(tab: TabId) {
    const tabDef = TABS.find((t) => t.id === tab);
    if (tabDef) {
      setJsonValues((prev) => ({ ...prev, [tab]: tabDef.template }));
      setParseErrors((prev) => ({ ...prev, [tab]: null }));
    }
  }

  function clearTab(tab: TabId) {
    setJsonValues((prev) => ({ ...prev, [tab]: '' }));
    setParseErrors((prev) => ({ ...prev, [tab]: null }));
    setSubmitState((prev) => ({ ...prev, [tab]: { status: 'idle' } }));
  }

  /* ---------- submit ---------- */

  async function handleSubmit(tab: TabId, formData?: unknown[]) {
    const data = formData ?? validateJson(tab);
    if (!data) return;
    if (!store.activeLocationId) return;

    setSubmitState((prev) => ({ ...prev, [tab]: { status: 'loading' } }));

    const locId = store.activeLocationId;
    const apiFns: Record<TabId, (locId: string, data: unknown[]) => Promise<unknown>> = {
      employees: api.bulkEmployees,
      menu: api.bulkMenuItems,
      orders: api.bulkOrders,
      shifts: api.bulkShifts,
    };

    try {
      const result: any = await apiFns[tab](locId, data);
      const created = result?.created ?? 0;
      const updated = result?.updated ?? 0;
      const skipped = result?.skipped ?? 0;
      setSubmitState((prev) => ({
        ...prev,
        [tab]: {
          status: 'success',
          message: `Created: ${created} | Updated: ${updated} | Skipped: ${skipped}`,
        },
      }));
      store.addToast({
        type: 'success',
        message: `${TABS.find((t) => t.id === tab)?.label}: Created ${created}, Updated ${updated}, Skipped ${skipped}`,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Submission failed';
      setSubmitState((prev) => ({
        ...prev,
        [tab]: { status: 'error', message: msg },
      }));
      store.addToast({ type: 'error', message: `${TABS.find((t) => t.id === tab)?.label}: ${msg}` });
    }
  }

  /* ---------- location creation ---------- */

  async function handleCreateLocation() {
    if (!newLocationName.trim()) {
      setLocationError('Location name is required.');
      return;
    }
    setLocationLoading(true);
    setLocationError(null);
    try {
      const loc = await api.createLocation({
        name: newLocationName.trim(),
        timezone: newLocationTimezone,
      });
      const locations = await api.getLocations();
      store.setLocations(locations);
      store.setActiveLocation(loc.id);
      setNewLocationName('');
      setShowCreateLocation(false);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to create location';
      setLocationError(msg);
    } finally {
      setLocationLoading(false);
    }
  }

  /* ---------- render ---------- */

  const currentTab = TABS.find((t) => t.id === activeTab)!;
  const CurrentIcon = currentTab.icon;
  const tabSubmit = submitState[activeTab];
  const tabError = parseErrors[activeTab];

  return (
    <div className="space-y-8">
      {/* Page header */}
      <div>
        <h1 className="text-xl font-bold text-gray-900">Data Input</h1>
        <p className="text-sm text-gray-500 mt-1">
          Import employees, menu items, orders, and shifts for your location.
        </p>
      </div>

      {/* ============ Location Setup ============ */}
      <section>
        <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-4">
          Location
        </h2>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-3 sm:p-5">
          {hasLocations && activeLocation && !showCreateLocation ? (
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <MapPin className="w-5 h-5 text-blue-500" />
                <div>
                  <p className="text-sm font-semibold text-gray-900">
                    {activeLocation.name}
                  </p>
                  <p className="text-xs text-gray-500">{activeLocation.timezone}</p>
                </div>
              </div>
              <button
                onClick={() => setShowCreateLocation(true)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 text-gray-700 text-xs font-medium rounded-lg hover:bg-gray-200 transition-colors duration-150 cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                Add location
              </button>
            </div>
          ) : hasLocations && !activeLocation && !showCreateLocation ? (
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm text-amber-600 font-medium">
                Select a location from the header dropdown to begin importing data.
              </p>
              <button
                onClick={() => setShowCreateLocation(true)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 text-gray-700 text-xs font-medium rounded-lg hover:bg-gray-200 transition-colors duration-150 cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                Add location
              </button>
            </div>
          ) : !showCreateLocation ? (
            <div className="text-center py-4">
              <MapPin className="w-8 h-8 text-gray-300 mx-auto mb-2" />
              <p className="text-sm text-gray-500 mb-3">
                No locations found. Create one to start importing data.
              </p>
              <button
                onClick={() => setShowCreateLocation(true)}
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors duration-150 cursor-pointer"
              >
                <Plus className="w-4 h-4" />
                Create Location
              </button>
            </div>
          ) : (
            <div className="space-y-4 max-w-full sm:max-w-md">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Location Name
                </label>
                <input
                  type="text"
                  value={newLocationName}
                  onChange={(e) => setNewLocationName(e.target.value)}
                  placeholder="e.g. Downtown Grill"
                  className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Timezone
                </label>
                <div className="relative">
                  <select
                    value={newLocationTimezone}
                    onChange={(e) => setNewLocationTimezone(e.target.value)}
                    className="w-full appearance-none px-3 py-2 pr-8 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent cursor-pointer"
                  >
                    {TIMEZONES.map((tz) => (
                      <option key={tz} value={tz}>
                        {tz}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                </div>
              </div>

              {locationError && (
                <p className="text-sm text-red-600">{locationError}</p>
              )}

              <div className="flex items-center gap-2">
                <button
                  onClick={handleCreateLocation}
                  disabled={locationLoading}
                  className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors duration-150 cursor-pointer"
                >
                  {locationLoading && (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  )}
                  Create
                </button>
                <button
                  onClick={() => {
                    setShowCreateLocation(false);
                    setLocationError(null);
                  }}
                  className="px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors duration-150 cursor-pointer"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* ============ Data Tabs ============ */}
      <section>
        <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-4">
          Bulk Import
        </h2>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          {/* Tab bar */}
          <div className="overflow-x-auto">
            <div className="flex border-b border-gray-200 min-w-max sm:min-w-0">
              {TABS.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;

                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`
                      flex items-center gap-1.5 sm:gap-2 px-3 sm:px-4 py-3 text-sm font-medium
                      border-b-2 transition-colors duration-150 cursor-pointer whitespace-nowrap
                      ${
                        isActive
                          ? 'border-blue-600 text-blue-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }
                    `}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Tab content */}
          <div className="p-3 sm:p-5">
            {/* Tab label + mode toggle + template/clear actions */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 sm:gap-3 mb-3">
              <div className="flex items-center gap-2 sm:gap-3">
                <CurrentIcon className="w-4 h-4 text-gray-400 shrink-0" />
                <span className="text-sm font-medium text-gray-700">
                  {currentTab.label}
                </span>
                <InputModeToggle mode={inputMode} onChange={setInputMode} />
              </div>
              {inputMode === 'json' && (
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => loadTemplate(activeTab)}
                    className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-gray-500 bg-gray-100 rounded hover:bg-gray-200 transition-colors duration-150 cursor-pointer"
                  >
                    <FileText className="w-3 h-3" />
                    Template
                  </button>
                  <button
                    onClick={() => clearTab(activeTab)}
                    className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-gray-500 bg-gray-100 rounded hover:bg-gray-200 transition-colors duration-150 cursor-pointer"
                  >
                    <Eraser className="w-3 h-3" />
                    Clear
                  </button>
                </div>
              )}
            </div>

            {/* Form mode */}
            {inputMode === 'form' && (
              <div>
                {activeTab === 'employees' && (
                  <EmployeeForm onSubmit={(data) => handleSubmit('employees', data)} />
                )}
                {activeTab === 'menu' && (
                  <MenuItemForm onSubmit={(data) => handleSubmit('menu', data)} />
                )}
                {activeTab === 'orders' && (
                  <OrderForm onSubmit={(data) => handleSubmit('orders', data)} />
                )}
                {activeTab === 'shifts' && (
                  <ShiftForm onSubmit={(data) => handleSubmit('shifts', data)} />
                )}
              </div>
            )}

            {/* JSON mode */}
            {inputMode === 'json' && (
              <>
                <textarea
                  value={jsonValues[activeTab]}
                  onChange={(e) => handleJsonChange(activeTab, e.target.value)}
                  placeholder={currentTab.placeholder}
                  rows={8}
                  spellCheck={false}
                  className={`
                    w-full px-4 py-3 bg-gray-900 text-gray-100 text-sm leading-relaxed
                    font-mono rounded-lg border-2 resize-y
                    placeholder-gray-600
                    focus:outline-none focus:ring-0
                    ${
                      tabError
                        ? 'border-red-500 focus:border-red-500'
                        : 'border-gray-700 focus:border-blue-500'
                    }
                  `}
                />

                {/* Parse error */}
                {tabError && (
                  <div className="mt-2 flex items-start gap-2 text-sm text-red-600">
                    <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                    <span>{tabError}</span>
                  </div>
                )}

                {/* Submit button */}
                <div className="mt-4 flex flex-wrap items-center gap-4">
                  <button
                    onClick={() => handleSubmit(activeTab)}
                    disabled={
                      tabSubmit.status === 'loading' || !store.activeLocationId
                    }
                    className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-150 cursor-pointer"
                  >
                    {tabSubmit.status === 'loading' ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Send className="w-4 h-4" />
                    )}
                    Submit
                  </button>

                  {!store.activeLocationId && (
                    <span className="text-xs text-amber-600 font-medium">
                      Select a location first
                    </span>
                  )}
                </div>
              </>
            )}

            {/* Submit result (shown in both modes) */}
            <div className="mt-3">
              {tabSubmit.status === 'success' && tabSubmit.message && (
                <span className="inline-flex items-center gap-1.5 text-sm text-emerald-600 font-medium">
                  <CheckCircle className="w-4 h-4" />
                  {tabSubmit.message}
                </span>
              )}

              {tabSubmit.status === 'error' && tabSubmit.message && (
                <span className="inline-flex items-center gap-1.5 text-sm text-red-600 font-medium">
                  <AlertTriangle className="w-4 h-4" />
                  {tabSubmit.message}
                </span>
              )}

              {tabSubmit.status === 'loading' && inputMode === 'form' && (
                <span className="inline-flex items-center gap-1.5 text-sm text-gray-500 font-medium">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Submitting...
                </span>
              )}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
