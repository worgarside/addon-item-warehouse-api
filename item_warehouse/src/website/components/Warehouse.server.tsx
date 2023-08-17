import React from "react";
import styles from "../styles/Warehouse.module.css";
import Item from "./Item.client";

const Warehouse: React.FC<{
  fields: string[];
  items: Record<string, string | number | boolean | null>[];
  warehouseName: string;
  currentPage: number;
}> = ({ fields, items, warehouseName, currentPage }) => {
  return (
    <div className={`p-0 m-0 mt-3 ${styles.container}`}>
      <table className={`table table-hover table-striped table-bordered`}>
        <thead className="thead-dark">
          <tr>
            {fields.map((header) => (
              <th scope="col" key={header} className="font-monospace">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {items.map(
            (
              item: Record<string, string | number | boolean | null>,
              index: number,
            ) => (
              <Item
                item={item}
                key={`${warehouseName}-${currentPage}-${index}`}
                index={index}
                warehouseName={warehouseName}
                currentPage={currentPage}
              />
            ),
          )}
        </tbody>
      </table>
    </div>
  );
};

export default Warehouse;
