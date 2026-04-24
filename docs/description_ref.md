<style>  
  .content-wrapper {
    max-height: 100px;
    overflow: hidden;
    position: relative;
    transition: max-height 0.3s ease-out;
  }
  
  .content-wrapper.expanded {
    max-height: 500px;
  }

  .read-more-button {
    display: block;
    margin-top: 15px;
    cursor: pointer;
    color: #736357;
  }
  
  .collapsible {
    background-color: #FBF9F7;
    color: #736357;
    cursor: pointer;
    padding: 20px 0px;
    width: 100%;
    border: none;
    text-align: left;
    font-size: 15px;
  }

  .collapsible:after {
    content: '\002B';
    color: #736357;
    font-weight: bold;
    float: right;
    margin-left: 5px;
  }

  .active:after {
    content: "\2212";
  }
  
  .content {
    padding: 0px 10px;
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.2s ease-out;
    background-color: #FBF9F7;
  }

</style>
<div id="myContent" class="content-wrapper">
  <!-- This is the Product Description -->
   <p>This chair stands out for its balanced design, with a wide, comfortable seat resting on a wooden base covered with oak veneer. The matte polyurethane finish protects the surface and adds warmth to the piece.<br><br>The wood is FSC™ 100% chain of custody certified with a responsible forest management model. The upholstery is made of small-structured chenille: soft to the touch, resistant to daily use and made of 100 % recycled polyester from a Global Recycled Standard certified supplier. This fabric contains a water-repellent treatment and is also OEKO-TEX® STANDARD 100 certified, which ensures safe and eco-friendly production.<br><br>It offers a medium-firm seat firmness thanks to the combination of webbing and springs with 55kg/m³ injection foam, which maintains the firmness and shape over time. Plus, the legs are fitted with felt protectors to prevent marks and scratches on the floor. A piece designed to last, functional in both domestic and commercial spaces.</p>
</div>
<span class="read-more-button" onclick="toggleReadMore()">+ More</span>
<br><br>
<!-- These are the dropdown tabs of information -->
<button class="collapsible">Details</button>
<div class="content">
  <!-- These are where the variant details go -->
  <h5>Designs Available</h5>
  <p>The Bosca Chair is available in 2 fabric colours and 2 different wood finishes.</p>
  <br>
  <h5>Fabric Colour</h5>
  <p>Terracotta Chenille</p>
  <br>
  <h5>Product Dimensions</h5>
  <p>Height: 76cm</p>
  <p>Width: 67cm</p>
  <p>Depth: 56cm</p>
  <p>Weight: 15kg</p>
  <br>
</div>
<!-- This is for the certifications and warranties (not all products have both) if not, just removed-->
<button class="collapsible">Certifications</button>
<div class="content"> 
  <h5>Certifications</h5>
  <p>FSC</p>
  <br> 
</div>
<br>

<!-- This is for the files (not all products have) if not, just removed-->

<button class="collapsible">Files</button>

<div class="content">
  <a href="https://presscloud.com/file/91/915725680692736/WOUD_Care_and_Maintenance.pdf">Care and Maintenance
  </a>
  <br>
  <a href="https://presscloud.com/file/49/490843997865145/UTILITY_SHELF_ASSEMBLY_INSTRUCTION.pdf">Assembly instructions
  </a>
</div>  
<script>
var coll = document.getElementsByClassName("collapsible");
var i;

for (i = 0; i < coll.length; i++) {
coll[i].addEventListener("click", function() {
this.classList.toggle("active");
var content = this.nextElementSibling;
if (content.style.maxHeight){
content.style.maxHeight = null;
} else {
content.style.maxHeight = content.scrollHeight + "px";
}
});
}

function toggleReadMore() {
const content = document.getElementById('myContent');
content.classList.toggle('expanded');
const button = document.querySelector('.read-more-button');
if (content.classList.contains('expanded')) {
button.textContent = 'Show Less';
} else {
button.textContent = '+ More';
}
}
</script>
