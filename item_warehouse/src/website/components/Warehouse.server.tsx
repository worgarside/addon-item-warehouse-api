import React from "react";
import { getItemsFromWarehouse, getWarehouseSchema } from "../services/api";
import styles from "../styles/Warehouse.module.css";
import Item from "./Item.client";

const Warehouse: React.FC<{ warehouseName: string }> = async ({
  warehouseName,
}) => {
  let items = [];
  try {
    items = await getItemsFromWarehouse(warehouseName);
  } catch (error) {
    return (
      <div className="alert alert-danger" role="alert">
        <h1>TODO: Error Page :(</h1>
        <pre>
          <code>{JSON.stringify(error, null, 2)}</code>
        </pre>
      </div>
    );
  }

  const schema = await getWarehouseSchema(warehouseName);
  const fields = Object.keys(schema);

  return (
    <>
      <h1>{warehouseName}</h1>
      <div className={`container p-0 m-0 ${styles.container}`}>
        <table
          className={`table table-hover table-striped table-bordered ${styles.table}`}
        >
          <thead className="thead-dark">
            <tr>
              {fields.map((header) => (
                <th scope="col" key={header}>
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {items.map((item: Record<string, ItemValue>, index: number) => (
              <Item item={item} key={index} index={index} />
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
};

export default Warehouse;
