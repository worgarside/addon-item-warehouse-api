"use client";

import ButtonGroup from "react-bootstrap/ButtonGroup";
import Dropdown from "react-bootstrap/Dropdown";
import DropdownButton from "react-bootstrap/DropdownButton";
import Cookie from "js-cookie";
import { useRouter, useSearchParams } from "next/navigation";

const PageSizeDropdown: React.FC<{
  currentPageSize: string;
  warehouseName: string;
}> = ({ currentPageSize, warehouseName }) => {
  const router = useRouter();

  const pageNumber = useSearchParams().get("page");

  return (
    <>
      <div>
        <DropdownButton
          as={ButtonGroup}
          id="page-size-dropdown"
          className="ms-3"
          size="sm"
          variant="secondary"
          title={`Page size: ${currentPageSize}`}
          onSelect={(eventKey: string | null) => {
            if (eventKey === null) {
              return;
            }
            Cookie.set("pageSize", eventKey);

            if (pageNumber !== null) {
              router.push(`/warehouse/${warehouseName}`);
            }

            router.refresh();
          }}
        >
          <Dropdown.Item eventKey="5">5</Dropdown.Item>
          <Dropdown.Item eventKey="10">10</Dropdown.Item>
          <Dropdown.Item eventKey="20">20</Dropdown.Item>
          <Dropdown.Item eventKey="30">30</Dropdown.Item>
          <Dropdown.Item eventKey="40">40</Dropdown.Item>
          <Dropdown.Item eventKey="50">50</Dropdown.Item>
          <Dropdown.Item eventKey="100">100</Dropdown.Item>
        </DropdownButton>
      </div>
    </>
  );
};

export default PageSizeDropdown;
