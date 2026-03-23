"use client";

import { BellIcon, ArrowPathIcon } from "@heroicons/react/24/outline";

export function Header() {
  return (
    <header className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-6">
      <div>
        <h1 className="text-lg font-semibold text-gray-900">
          Persönliches Projektmanagement
        </h1>
      </div>
      <div className="flex items-center gap-4">
        <button
          className="rounded-lg p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700"
          title="Synchronisieren"
        >
          <ArrowPathIcon className="h-5 w-5" />
        </button>
        <button
          className="relative rounded-lg p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700"
          title="Benachrichtigungen"
        >
          <BellIcon className="h-5 w-5" />
          <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-red-500" />
        </button>
      </div>
    </header>
  );
}
