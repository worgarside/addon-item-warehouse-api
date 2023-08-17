"use client";

import { useRouter } from "next/navigation";
import React from "react";
import Pagination from "react-bootstrap/Pagination";

const Paginator: React.FC<{
  currentPage: number;
  totalPages: number;
  warehouseName: string;
}> = ({ currentPage, totalPages, warehouseName }) => {
  const router = useRouter();
  const items = [];

  for (let number = 1; number <= totalPages; number++) {
    items.push(
      <Pagination.Item
        key={number}
        active={number === currentPage}
        onClick={() => {
          router.push(`/warehouse/${warehouseName}?page=${number}`);
          router.refresh();
        }}
      >
        {number}
      </Pagination.Item>,
    );

    // if (number === 1) {
    //   if (currentPage > 3) {
    //     items.push(<Pagination.Ellipsis key="ellipsis-first" />);
    //   }
    // }
  }

  return (
    <Pagination size="sm" className="mt-3">
      {items}
    </Pagination>
  );
};

export default Paginator;
