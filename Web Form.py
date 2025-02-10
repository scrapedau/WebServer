<!-- Building Type -->
  <div>
    <label for="building_type">Building Type</label>
    <select id="building_type" name="building_type[]" multiple required>
      <option value="house">House</option>
      <option value="apartment">Apartment</option>
      <option value="townhouse">Townhouse</option>
      <option value="new_house_and_land">New House & Land</option>
      <option value="vacant_land">Vacant Land</option>
      <option value="farm">Farm</option>
      <option value="acreage">Acreage / Semi-rural</option>
      <option value="retirement_living">Retirement Living</option>
      <option value="block_of_units">Block of Units</option>
      <option value="rural">Rural</option>
    </select>
    <div id="tags"></div>
  </div>
  </div>
added
<script>
  document.addEventListener('DOMContentLoaded', function () {
    const selectElement = document.getElementById('building_type');
    const tagsContainer = document.getElementById('tags');

    const selectedValues = new Set();

    selectElement.addEventListener('change', function (event) {
      const selectedOptions = Array.from(selectElement.selectedOptions);
      const currentValues = selectedOptions.map(option => option.value);
      selectedValues.clear();
      currentValues.forEach(value => selectedValues.add(value));
      updateTags();
    });

    function updateTags() {
      tagsContainer.innerHTML = '';
      selectedValues.forEach(value => {
        const tag = document.createElement('span');
        tag.className = 'tag';
        tag.textContent = value;

        const removeButton = document.createElement('button');
        removeButton.className = 'remove';
        removeButton.textContent = 'x';
        removeButton.addEventListener('click', function () {
          selectedValues.delete(value);
          updateTags();
          Array.from(selectElement.options).forEach(option => {
            if (option.value === value) option.selected = false;
          });
        });
        tag.appendChild(removeButton);
        tagsContainer.appendChild(tag);
      });
    }
  });
</script>

<style>
  #tags {
    display: flex;
    flex-wrap: wrap;
    margin-top: 0.5rem;
  }
  .tag {
    background-color: #e0e0e0;
    border: 1px solid #d0d0d0;
    border-radius: 3px;
    padding: 0.5rem;
    margin: 0.2rem;
    display: flex;
    align-items: center;
  }
  .tag .remove {
    margin-left: 0.5rem;
    background: none;
    border: none;
    font-size: 0.8rem;
    cursor: pointer;
  }
  .tag .remove:hover {
    color: red;
  }
</style>
