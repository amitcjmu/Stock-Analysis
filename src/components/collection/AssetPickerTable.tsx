/**
 * AssetPickerTable Component
 *
 * Reusable table for multi-asset selection with server-side pagination,
 * search, sorting, and bulk selection controls.
 *
 * Features:
 * - Server-side pagination for large asset lists
 * - Multi-select checkboxes with "Select All on Page"
 * - Search with 500ms debounce
 * - Column sorting (name, type, progress)
 * - Clear selection action
 */

import React, { useState, useEffect, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { collectionFlowApi } from "@/services/api/collection-flow";

export interface Asset {
  id: string;
  name: string;
  type: "application" | "server" | "database";
  progress_percent: number;
  completeness_score?: number;
}

export interface AssetPickerTableProps {
  flow_id: string;
  selected_asset_ids: string[];
  on_selection_change: (asset_ids: string[]) => void;
  asset_filter?: (asset: Asset) => boolean;
  max_selection?: number;
}

type SortField = "name" | "type" | "progress_percent";
type SortDirection = "asc" | "desc";

export const AssetPickerTable: React.FC<AssetPickerTableProps> = ({
  flow_id,
  selected_asset_ids,
  on_selection_change,
  asset_filter,
  max_selection,
}) => {
  const [search_query, set_search_query] = useState("");
  const [debounced_search, set_debounced_search] = useState("");
  const [current_page, set_current_page] = useState(1);
  const [sort_field, set_sort_field] = useState<SortField>("name");
  const [sort_direction, set_sort_direction] = useState<SortDirection>("asc");

  const page_size = 20;

  // Debounce search input (500ms)
  useEffect(() => {
    const timer = setTimeout(() => {
      set_debounced_search(search_query);
      set_current_page(1); // Reset to first page on search
    }, 500);

    return () => clearTimeout(timer);
  }, [search_query]);

  // TODO: Replace with actual API endpoint when available
  // For now, using flow questionnaires as a placeholder
  const { data: flow_data, isLoading } = useQuery({
    queryKey: ["collection-assets", flow_id],
    queryFn: () => collectionFlowApi.getFlowDetails(flow_id),
    enabled: !!flow_id,
  });

  // Extract and process assets from flow data
  const all_assets: Asset[] = React.useMemo(() => {
    // TODO: Replace with actual asset data from API
    // This is a placeholder implementation
    if (!flow_data) return [];

    // Mock asset data for development
    return [];
  }, [flow_data]);

  // Apply search, filter, and sorting
  const filtered_assets = React.useMemo(() => {
    let result = [...all_assets];

    // Apply search filter
    if (debounced_search) {
      const query = debounced_search.toLowerCase();
      result = result.filter((asset) =>
        asset.name.toLowerCase().includes(query) ||
        asset.type.toLowerCase().includes(query)
      );
    }

    // Apply custom filter if provided
    if (asset_filter) {
      result = result.filter(asset_filter);
    }

    // Apply sorting
    result.sort((a, b) => {
      let comparison = 0;

      if (sort_field === "name") {
        comparison = a.name.localeCompare(b.name);
      } else if (sort_field === "type") {
        comparison = a.type.localeCompare(b.type);
      } else if (sort_field === "progress_percent") {
        comparison = a.progress_percent - b.progress_percent;
      }

      return sort_direction === "asc" ? comparison : -comparison;
    });

    return result;
  }, [all_assets, debounced_search, asset_filter, sort_field, sort_direction]);

  // Paginate results
  const total_pages = Math.ceil(filtered_assets.length / page_size);
  const page_assets = filtered_assets.slice(
    (current_page - 1) * page_size,
    current_page * page_size
  );

  // Get assets on current page
  const page_asset_ids = page_assets.map((a) => a.id);

  // Check if all on page are selected
  const all_on_page_selected =
    page_asset_ids.length > 0 &&
    page_asset_ids.every((id) => selected_asset_ids.includes(id));

  // Handle select/deselect all on page
  const handle_select_all_on_page = useCallback(() => {
    if (all_on_page_selected) {
      // Deselect all on current page
      const new_selection = selected_asset_ids.filter(
        (id) => !page_asset_ids.includes(id)
      );
      on_selection_change(new_selection);
    } else {
      // Select all on current page
      const new_selection = [
        ...selected_asset_ids,
        ...page_asset_ids.filter((id) => !selected_asset_ids.includes(id)),
      ];

      // Respect max_selection limit
      if (max_selection && new_selection.length > max_selection) {
        alert(`Maximum ${max_selection} assets can be selected`);
        return;
      }

      on_selection_change(new_selection);
    }
  }, [all_on_page_selected, selected_asset_ids, page_asset_ids, on_selection_change, max_selection]);

  // Handle individual asset selection
  const handle_asset_toggle = useCallback(
    (asset_id: string) => {
      const is_selected = selected_asset_ids.includes(asset_id);

      if (is_selected) {
        on_selection_change(selected_asset_ids.filter((id) => id !== asset_id));
      } else {
        if (max_selection && selected_asset_ids.length >= max_selection) {
          alert(`Maximum ${max_selection} assets can be selected`);
          return;
        }
        on_selection_change([...selected_asset_ids, asset_id]);
      }
    },
    [selected_asset_ids, on_selection_change, max_selection]
  );

  // Handle clear all selections
  const handle_clear_selection = useCallback(() => {
    on_selection_change([]);
  }, [on_selection_change]);

  // Handle column header click for sorting
  const handle_sort = useCallback(
    (field: SortField) => {
      if (sort_field === field) {
        // Toggle direction if same field
        set_sort_direction((prev) => (prev === "asc" ? "desc" : "asc"));
      } else {
        // New field - default to ascending
        set_sort_field(field);
        set_sort_direction("asc");
      }
    },
    [sort_field]
  );

  // Render sort indicator
  const render_sort_indicator = (field: SortField) => {
    if (sort_field !== field) return null;
    return sort_direction === "asc" ? " ↑" : " ↓";
  };

  if (isLoading) {
    return <div className="p-4 text-center">Loading assets...</div>;
  }

  return (
    <div className="space-y-4">
      {/* Search and Actions Row */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex-1 max-w-md">
          <input
            type="text"
            placeholder="Search assets..."
            value={search_query}
            onChange={(e) => set_search_query(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">
            {selected_asset_ids.length} selected
            {max_selection && ` (max: ${max_selection})`}
          </span>
          {selected_asset_ids.length > 0 && (
            <button
              onClick={handle_clear_selection}
              className="px-3 py-1 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 rounded"
            >
              Clear Selection
            </button>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left">
                <input
                  type="checkbox"
                  checked={all_on_page_selected}
                  onChange={handle_select_all_on_page}
                  disabled={page_assets.length === 0}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
              </th>
              <th
                onClick={() => handle_sort("name")}
                className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              >
                Name{render_sort_indicator("name")}
              </th>
              <th
                onClick={() => handle_sort("type")}
                className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              >
                Type{render_sort_indicator("type")}
              </th>
              <th
                onClick={() => handle_sort("progress_percent")}
                className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              >
                Progress{render_sort_indicator("progress_percent")}
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {page_assets.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-gray-500">
                  {search_query
                    ? "No assets match your search"
                    : "No assets available"}
                </td>
              </tr>
            ) : (
              page_assets.map((asset) => (
                <tr
                  key={asset.id}
                  className={`hover:bg-gray-50 ${
                    selected_asset_ids.includes(asset.id) ? "bg-blue-50" : ""
                  }`}
                >
                  <td className="px-4 py-3">
                    <input
                      type="checkbox"
                      checked={selected_asset_ids.includes(asset.id)}
                      onChange={() => handle_asset_toggle(asset.id)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                  </td>
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">
                    {asset.name}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500 capitalize">
                    {asset.type}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-200 rounded-full h-2 max-w-[100px]">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${asset.progress_percent}%` }}
                        />
                      </div>
                      <span className="text-xs">{asset.progress_percent}%</span>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {total_pages > 1 && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-600">
            Showing {(current_page - 1) * page_size + 1} to{" "}
            {Math.min(current_page * page_size, filtered_assets.length)} of{" "}
            {filtered_assets.length} assets
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => set_current_page((p) => Math.max(1, p - 1))}
              disabled={current_page === 1}
              className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <span className="px-3 py-1 text-sm">
              Page {current_page} of {total_pages}
            </span>
            <button
              onClick={() =>
                set_current_page((p) => Math.min(total_pages, p + 1))
              }
              disabled={current_page === total_pages}
              className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
