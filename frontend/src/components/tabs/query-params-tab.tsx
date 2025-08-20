import { useContext } from "react";
import { AppContext } from "../../context/AppContext";
import { Button } from "../ui/button";
import InputTemplate from "../ui/input-template";

const QueryParamsTab = () => {
  const { queryParams, handleAdd } = useContext(AppContext);
  const type = "queryParams";

  return (
    <div id="query-params" className="w-full h-full">
      {queryParams.map((item) => (
        <InputTemplate key={item.id} item={item} type={type} />
      ))}
      <Button type="button" className="mt-2" onClick={() => handleAdd(type)}>
        Add
      </Button>
    </div>
  );
};

export default QueryParamsTab;
