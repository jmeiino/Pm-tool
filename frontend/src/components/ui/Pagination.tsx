"use client";

import { Button } from "./Button";
import { ChevronLeftIcon, ChevronRightIcon } from "@heroicons/react/24/outline";

interface PaginationProps {
  count: number;
  pageSize?: number;
  currentPage: number;
  onPageChange: (page: number) => void;
}

export function Pagination({
  count,
  pageSize = 25,
  currentPage,
  onPageChange,
}: PaginationProps) {
  const totalPages = Math.ceil(count / pageSize);

  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-between border-t border-gray-200 pt-4">
      <p className="text-sm text-gray-500">
        Seite {currentPage} von {totalPages} ({count} Einträge)
      </p>
      <div className="flex items-center gap-2">
        <Button
          variant="secondary"
          size="sm"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage <= 1}
        >
          <ChevronLeftIcon className="h-4 w-4" />
          Zurück
        </Button>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage >= totalPages}
        >
          Weiter
          <ChevronRightIcon className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
