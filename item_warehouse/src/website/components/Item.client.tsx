import React from "react";
import Cell from "./Cell.client";

interface ItemProps {
  item: Record<string, boolean | number | string | null>;
  index: number;
  currentPage: number;
  warehouseName: string;
}

const Item: React.FC<ItemProps> = ({
  item,
  index,
  currentPage,
  warehouseName,
}) => {
  return (
    <tr key={index}>
      {Object.entries(item).map(([key, value], cellIndex) => (
        <Cell
          value={value}
          header={key}
          key={`${warehouseName}-${currentPage}-${index}-${cellIndex}`}
        />
      ))}
    </tr>
  );
};

export default Item;
