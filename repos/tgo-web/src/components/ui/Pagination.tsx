import React from 'react';
import Icon from './Icon';

interface PaginationProps {
  currentPage?: number;
  totalPages?: number;
  onPageChange?: (page: number) => void;
  className?: string;
}

/**
 * Pagination component
 */
const Pagination: React.FC<PaginationProps> = ({ 
  currentPage = 1, 
  totalPages = 10, 
  onPageChange,
  className = '' 
}) => {
  const handlePageClick = (page: number): void => {
    if (page !== currentPage && page >= 1 && page <= totalPages) {
      onPageChange?.(page);
    }
  };

  const renderPageNumbers = (): React.ReactNode[] => {
    const pages: React.ReactNode[] = [];
    const showEllipsis = totalPages > 7;
    
    if (!showEllipsis) {
      // Show all pages if total is 7 or less
      for (let i = 1; i <= totalPages; i++) {
        pages.push(
          <button
            key={i}
            onClick={() => handlePageClick(i)}
            className={`
              relative inline-flex items-center px-4 py-2 border-r border-gray-300 text-sm font-medium transition-colors
              ${i === currentPage 
                ? 'z-10 bg-blue-500 border-blue-500 text-white' 
                : 'text-gray-500 hover:bg-gray-50'
              }
            `}
          >
            {i}
          </button>
        );
      }
    } else {
      // Show abbreviated pagination
      pages.push(
        <button
          key={1}
          onClick={() => handlePageClick(1)}
          className={`
            relative inline-flex items-center px-4 py-2 border-r border-gray-300 text-sm font-medium transition-colors
            ${1 === currentPage 
              ? 'z-10 bg-blue-500 border-blue-500 text-white' 
              : 'text-gray-500 hover:bg-gray-50'
            }
          `}
        >
          1
        </button>
      );

      if (currentPage > 3) {
        pages.push(
          <span key="ellipsis1" className="relative inline-flex items-center px-4 py-2 border-r border-gray-300 text-sm font-medium text-gray-700">
            ...
          </span>
        );
      }

      // Show current page and neighbors
      const start = Math.max(2, currentPage - 1);
      const end = Math.min(totalPages - 1, currentPage + 1);
      
      for (let i = start; i <= end; i++) {
        if (i !== 1 && i !== totalPages) {
          pages.push(
            <button
              key={i}
              onClick={() => handlePageClick(i)}
              className={`
                relative inline-flex items-center px-4 py-2 border-r border-gray-300 text-sm font-medium transition-colors
                ${i === currentPage 
                  ? 'z-10 bg-blue-500 border-blue-500 text-white' 
                  : 'text-gray-500 hover:bg-gray-50'
                }
              `}
            >
              {i}
            </button>
          );
        }
      }

      if (currentPage < totalPages - 2) {
        pages.push(
          <span key="ellipsis2" className="relative inline-flex items-center px-4 py-2 border-r border-gray-300 text-sm font-medium text-gray-700">
            ...
          </span>
        );
      }

      if (totalPages > 1) {
        pages.push(
          <button
            key={totalPages}
            onClick={() => handlePageClick(totalPages)}
            className={`
              relative inline-flex items-center px-4 py-2 border-r border-gray-300 text-sm font-medium transition-colors
              ${totalPages === currentPage 
                ? 'z-10 bg-blue-500 border-blue-500 text-white' 
                : 'text-gray-500 hover:bg-gray-50'
              }
            `}
          >
            {totalPages}
          </button>
        );
      }
    }

    return pages;
  };

  return (
    <nav className={`inline-flex rounded-md shadow-sm -space-x-px bg-white border border-gray-300 ${className}`} aria-label="Pagination">
      {/* Previous Button */}
      <button
        onClick={() => handlePageClick(currentPage - 1)}
        disabled={currentPage === 1}
        className="relative inline-flex items-center px-2 py-2 rounded-l-md border-r border-gray-300 text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        <span className="sr-only">Previous</span>
        <Icon name="ChevronLeft" size={20} />
      </button>

      {/* Page Numbers */}
      {renderPageNumbers()}

      {/* Next Button */}
      <button
        onClick={() => handlePageClick(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="relative inline-flex items-center px-2 py-2 rounded-r-md text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        <span className="sr-only">Next</span>
        <Icon name="ChevronRight" size={20} />
      </button>
    </nav>
  );
};

export default Pagination;
